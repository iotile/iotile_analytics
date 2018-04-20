import os
import json
import zipfile
import shutil
from datetime import datetime
from jinja2 import Environment, PackageLoader, contextfunction, Markup
from iotile_analytics.core.exceptions import UsageError
from future.utils import viewitems
from bokeh.embed import file_html
from bokeh.resources import Resources
from ..app import AnalyticsObject


@contextfunction
def include_file(ctx, name):
    """Jinja2 function to allow including literal files into a template.

    This is used for emdedding jquery into our unhosted reports.
    """

    env = ctx.environment
    return Markup(env.loader.get_source(env, name)[0])


class LiveReport(AnalyticsObject):
    """Base class for all dynamic html documents that can be exported.

    A LiveReport is basically a Bokeh embedded document that can reference
    external files.  If external files are referenced, they must be done so
    using one of the primitive methods defined by this class so that we are
    able to properly export the files in a way that allows them to be loaded
    outside of the context of a bokeh application or notebook.

    Structuring a Bokeh documentat so that we can export it is the primary job
    of the LiveReport class.  The primary difference between a LiveReport and
    a standard embedded Bokeh document is the method by which a LiveReport is
    able to reference a tree of local files and load them into
    ColumnDataSource objects without needing a web browser.

    Args:
        target (int): Whether we are targetting a hosted or unhosted environment
            so that we generate the appropriate content.
    """

    # Export targets
    UNHOSTED = 0
    HOSTED = 1

    def __init__(self, target):
        self.models = []
        self.title = "Unnamed Live Report"
        self.external_files = {}
        self.loadable_models = {}
        self.target = target
        self._relative_dir = "data"

        # Internal template variables that subclasses can override to insert details into the
        # template.

        self.header = None
        self.before_content = None
        self.after_content = None
        self.footer = None

        self.extra_scripts = []
        self.extra_css = []

    @property
    def standalone(self):
        return len(self.external_files) == 0

    def mark_loadable_source(self, source, loadable_options, columns):
        """Mark a ColumnDataSource as externally loadable.

        This function returns the name of a javascript function that takes a
        single argument and loads the passed data source with one of the
        loadable options given its dictionary key which should be string or
        an integer that will be formated in decimal and used as a file name.
        """

        ref = source.ref
        model_id = ref['id']
        safe_model_id = model_id.replace('-', '_')

        func_name = "load_model_{}".format(safe_model_id)
        trigger_name = "trigger_load_{}".format(safe_model_id)

        for name, values in viewitems(loadable_options):
            file_name = "{}_{}".format(safe_model_id, name)

            file_obj = {
                'name': file_name,
                'columns': columns,
                'id': model_id,
                'data': values,
                'func': func_name
            }

            self.external_files[file_name] = file_obj

        self.loadable_models[model_id] = {
            'trigger_function': trigger_name,
            'load_function': func_name,
            'safe_id': safe_model_id
        }

        return trigger_name

    def render_jsonp(self, path, info):
        """Render a dictionary as a jsonp file.

        These files are suitable for loading from a local filesystem so they
        can be used for unhosted LiveReports that are just opened in a web
        browser.

        Args:
            path (str): The path at which to save the resulting jsonp file.
            info (dict): An info dictionary as created by the mark_loadable_source
                function.
        """

        json_data = json.dumps(info['data'])

        with open(path, "wb") as outfile:
            write_data = "{}({});".format(info['func'], json_data)
            outfile.write(write_data.encode('utf-8'))

    @classmethod
    def find_template(cls, package, folder, name):
        """Find a template inside package data.

        This helper function will find a jinja2 template for you by looking
        inside a data inside an installed package.

        Args:
            package (str): A dotted package name for the subpackage that
                contains folder, which should not have an __init__.py file
            folder (str): The name of the folder that contains the templates
                and is located in the installed subpackage specified by package.
            name (str): The name of the template that we wish to load.

        Returns:
            jinja2.Template: The loaded template.
        """

        env = Environment(loader=PackageLoader(package, folder))
        template = env.get_template(name)
        return template

    def render(self, output_path, bundle=False):
        """Render this report to output_path.

        If this report is a standalone html file, the output path
        will have .html appended to it and be a single file.

        If this report is not standalone, the output will be
        folder that is created at output_path.

        If bundle is True and the report is not standalone, it will be zipped
        into a file at output_path.zip.  Any html or directory that was
        created as an intermediary before zipping will be deleted before this
        function returns.

        Args:
            output_path (str): the path to the folder that we wish
                to create.

        Returns:
            str: The path to the actual file or directory created.  This
                may differ from the file you pass in output_path by an
                extension or the addition of a subdirectory.
        """

        if output_path is None:
            raise ValueError("You must pass an output_path to render this LiveReport")

        # Make sure we have the path stem
        if output_path.endswith(".html"):
            output_path = output_path[:-5]

        if self.standalone:
            html_path = output_path + ".html"
            bundle_path = output_path + ".zip"
        else:
            os.makedirs(output_path)
            html_path = os.path.join(output_path, 'index.html')
            bundle_path = output_path + ".zip"

        env = Environment(loader=PackageLoader('iotile_analytics.interactive.reports', 'templates'))
        env.globals['include_file'] = include_file

        if self.target == self.UNHOSTED:
            template = env.get_template('unhosted_file.html')
        else:
            template = env.get_template('hosted_file.html')

        template_vars = {
            'loadable_models': self.loadable_models,
            'timestamp': datetime.utcnow().isoformat(),
            'header': self.header,
            'before_content': self.before_content,
            'after_content': self.after_content,
            'footer': self.footer,
            'extra_scripts': self.extra_scripts
        }

        rendered_html = file_html(self.models, Resources('inline'), self.title, template, template_vars)

        with open(html_path, "wb") as outfile:
            outfile.write(rendered_html)

        if not self.standalone:
            datadir = os.path.join(output_path, "data")
            os.makedirs(datadir)

            for filename, fileinfo in viewitems(self.external_files):
                file_path = os.path.join(datadir, filename)

                if self.target == self.UNHOSTED:
                    self.render_jsonp(file_path + ".jsonp", fileinfo)
                else:
                    raise UsageError("HOSTED mode for LiveReports is not yet supported")

        # If we're told to bundle, zip up everything and return the path to zip file created
        # instead of the rendered html
        if bundle:
            if self.standalone:
                zip_obj = zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED)
                zip_obj.write(html_path, os.path.basename(html_path))
                os.remove(html_path)
            else:
                shutil.make_archive(output_path, "zip", os.path.join(output_path, '..'), os.path.relpath(output_path, start=os.path.join(output_path, '..')))
                shutil.rmtree(output_path)
            return bundle_path

        return html_path
