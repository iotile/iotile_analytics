"""Default implementation for a bokeh application that can show itself in a server or notebook."""

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.io import show as bokeh_show
from iotile_analytics.core.exceptions import UsageError


class AnalyticsObject(object):
    """Base class for all objects that can be added to an AnalyticsApplication.

    These objects must have a root property that returns a Model or LayoutDOM
    object that corresponds to the root object that should be added to the
    application.
    """

    pass


class AnalyticsApplication(Application):
    """Base class for Bokeh applications built from iotile_analytics objects."""

    def __init__(self, *objects):
        for obj in objects:
            if not isinstance(obj, AnalyticsObject):
                raise UsageError("You must only pass AnalyticsObject subclasses to an AnalyticsApplication", object=obj, type=type(obj))

        self.roots = objects

        super(AnalyticsApplication, self).__init__(FunctionHandler(self._modify_document_with_roots))

    def _modify_document_with_roots(self, doc):
        for obj in self.roots:
            doc.add_root(obj.root)



def show(analytics_obj, interactive=True, **kwargs):
    """Show an application or analytics object in a notebook.

    This function will ultimately call bokeh.io.show() to actually show the
    object and with either wrap it inside an AnalyticsApplication object in
    order to have python callbacks work (if interactive==True, which is
    the default behavior) or it will just show the root Model objects without
    a bokeh server if interactive==False.

    Args:
        analytics_obj (AnalyticsApplication or AnalyticsObject): The object that we
            wish to show.  If this is an AnalyticsObject and noninteractive
    """

    objs_to_show = []
    if isinstance(analytics_obj, AnalyticsApplication):
        if not interactive:
            objs_to_show = [x.root for x in analytics_obj.roots]
        else:
            objs_to_show = [analytics_obj]

    elif isinstance(analytics_obj, AnalyticsObject):
        if not interactive:
            objs_to_show = [analytics_obj.root]
        else:
            objs_to_show = [AnalyticsApplication(analytics_obj)]
    else:
        raise UsageError("You must pass either an AnalyticsObject or AnalyticsApplication subclass to show()",
                         object=analytics_obj, type=type(analytics_obj))

    for obj in objs_to_show:
        bokeh_show(obj, **kwargs)
