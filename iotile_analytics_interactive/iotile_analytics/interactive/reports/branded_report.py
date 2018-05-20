"""A base class for reports that include a nice Arch header and footer."""

from .report import LiveReport

APP_IOTILE_CLOUD = "https://app.iotile.cloud"


class BrandedReport(LiveReport):
    """LiveReport base class with fancy header and footer.

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
        super(BrandedReport, self).__init__(target)
        self.header = self._render_branding("branded_header.html", source_info, link_url)
        self.footer = self._render_branding("branded_footer.html", source_info, link_url)

    def _render_branding(self, template_name, source_info, link_url):
        template = self.find_template('iotile_analytics.interactive.reports', 'templates', template_name)

        # Handling labeling for archives and devices
        label = source_info.get('title')
        if label is None:
            label = source_info.get('label')

        if label is None:
            label = "unknown"

        args = {
            "org_slug": source_info.get('org', "unknown"),
            "label": label,
            "link_url": link_url,
            "source": source_info
        }

        return template.render(args)
