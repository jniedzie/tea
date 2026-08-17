from ROOT import TLegend
from dataclasses import dataclass


@dataclass
class Legend:
    x1: float = 0.1
    y1: float = 0.1
    x2: float = 0.5
    y2: float = 0.5
    options: str = ""
    title: str = ""
    text_size: float = 20
    fill_color: int = None

    def getRootLegend(self):
        legend = TLegend(self.x1, self.y1, self.x2, self.y2)
        self.__setupLegend(legend)
        return legend

    def __setupLegend(self, legend):
        legend.SetBorderSize(0)
        # Keep the plot visible behind the legend by default.  A fill color
        # opts back into a solid legend background for users who need one.
        legend.SetFillStyle(0)
        if self.fill_color is not None:
            legend.SetFillColor(self.fill_color)
            legend.SetFillStyle(1001)
        legend.SetTextFont(43)
        legend.SetTextSize(self.text_size)

        # set legend title
        if self.title != "":
            legend.SetHeader(self.title)
