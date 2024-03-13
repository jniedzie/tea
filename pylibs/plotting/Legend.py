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

    def getRootLegend(self):
        legend = TLegend(self.x1, self.y1, self.x2, self.y2)
        self.__setupLegend(legend)
        return legend

    def __setupLegend(self, legend):
        legend.SetBorderSize(0)
        # legend.SetFillColor(0)
        # legend.SetFillStyle(0)
        legend.SetTextFont(42)
        legend.SetTextSize(0.035)

        # set legend title
        if self.title != "":
            legend.SetHeader(self.title)
