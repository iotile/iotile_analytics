"""Helper classes showing interactive piechart."""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from .viewer_base import BaseViewer


class PieViewer(BaseViewer):
    """A piechart viewer based on wedge() Glyph.

    All functionality in BaseViewer is present and there are a few
    convenience functions for setting the tick format on the axes
    easily.

    Apart from the special arguments listed below, all other arguments
    are passed through to BaseViewer.

    Args:

    """

    def __init__(self, **kwargs):

        if 'x_type' not in kwargs:
            kwargs['x_type'] = 'auto'

        if 'y_type' not in kwargs:
            kwargs['y_type'] = 'auto'

        super(PieViewer, self).__init__(**kwargs)


    def add_pie(self, x, y, radius, start_angle, end_angle, line_color, fill_color, source, legend=None):
        """A method to add histogram to bokeh figure.

        Args:
            x: x-coordinate of the points of the wedges
            y: y-coordinate of the points of the wedges
            radius: Radii of the wedges
            start_angle: The angles to start the wedges, as measured from the horizontal
            end_angle: The angles to end the wedges, as measured from the horizontal
            line_color: Color of the line separating the wedges
            fill_color: name of the column in the source which contains the colors
                        corresponding to wedges
            legend: name of the column in the source that contains names corresponding
                    to the wedges in

        Returns:
            render: A rendered Glyph based on options chosen

        """
        render = self.figure.wedge(x=x, y=y, radius=radius, start_angle=start_angle,
                                   end_angle=end_angle, line_color=line_color, fill_color='color',
                                   source=source, legend=legend)

        return render
