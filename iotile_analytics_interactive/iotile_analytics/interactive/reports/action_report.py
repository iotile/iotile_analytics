from collections import namedtuple
from jinja2 import Environment
from .branded_report import BrandedReport, APP_IOTILE_CLOUD


ActionLink = namedtuple("ActionLink", ["link", "link_text", "short_desc", "help_text"])


BEFORE_CONTENT = r"""
<div class="before-content">
    {{ before_table }}
    {% if actions | length > 0 %}
    <table class="action-table">
      <col width="30%" />
      <col width="70%" />
      <tr class="action-table-header">
            <th>
                Action
            </th>
            <th>
                Description
            </th>
        </tr>
        <tbody>
        {% for action in actions %}
          <tr class="action-table-row">
            <th>
            <div>
             <a href="{{action.link}}">{{ action.link_text }}</a>
            </div>
            {% if action.help_text is not none %}
              <div class="action-tooltip">
                ?
                <span class="tooltiptext">{{ action.help_text }}</span>
              </div>
            {% endif %}
            </th>
            <th>
                {{ action.short_desc }}
            </th>
          </tr>
        {% endfor %}
        </tbody>
    </table>
    {% endif %}
    {{ after_table }}
</div>
"""

class ActionReport(BrandedReport):
    """A branded live report with a table of action links.

    The action links are rendered in a nice table format with a link, a short
    description and a longer description available as a tooltip on hover.

    This report class is suitable for generating reports that contain
    links to specific next-steps, such as archiving a trip or resetting
    a device.

    By default, only a table is shown.  You can customize what comes before
    and after the table by assigning to the ``before_table`` and ``after_table``
    members.

    Args:
        target (int): Whether we are targetting a hosted or unhosted environment
            so that we generate the appropriate content.
        source_info (dict): A dictionary of source information obtained from an
            analysis group that allows us to setup the correct header and footer
            information.
        link_url (str): An optional direct link to the object that we are showing
            a report about in app.iotile.cloud.  If not passed it defaults to
            the generic start page of app.iotile.cloud.
    """

    def __init__(self, target, source_info, link_url=APP_IOTILE_CLOUD):
        super(ActionReport, self).__init__(target, source_info, link_url)

        self.before_table = ""
        self.after_table = ""
        self.actions = []

    def add_action(self, link, target, desc, help_text=None):
        """Add an action to the action table.

        The action will be shown as a row in the table with the link
        and the short description.  The help text will be available by
        hovering over a ? icon after the link as a tooltip.

        Args:
            link (str): The text that should be shown in the link.
            target (str): The link target href.
            desc (str): A short one line description
            help_text (str): A longer description that will be shown in a
                tooltip when the user hovers.  If you do not specify any
                help text, no tool tip will be shown.
        """

        action = ActionLink(target, link, desc, help_text)
        self.actions.append(action)

    def prepare_render(self):
        """Create the action table before we render the rest of the document."""

        args = {
            "actions": self.actions,
            "before_table": self.before_table,
            "after_table": self.after_table
        }

        env = Environment()
        template = env.from_string(BEFORE_CONTENT)

        self.before_content = template.render(args)
