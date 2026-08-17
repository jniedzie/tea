import ROOT
import ctypes
from enum import Enum


class CmsLabel(Enum):
    """Allowed CMS plot labels from the CMS plotting guidelines."""

    paper = ("CMS", None)
    paper_sim = ("CMS", "Simulation")
    paper_supplementary = ("CMS", "Supplementary")
    paper_sim_supplementary = ("CMS", "Simulation Supplementary")
    pas = ("CMS", "Preliminary")
    pas_sim = ("CMS", "Simulation Preliminary")
    pas_supplementary = ("CMS", "Preliminary")
    pas_sim_supplementary = ("CMS", "Simulation Preliminary")
    thesis = ("CMS", "Work in progress")
    thesis_sim = ("CMS", "Simulation Work in progress")
    private_data_sim = (None, "Private work (CMS data/simulation)")
    private_data = (None, "Private work (CMS data)")
    private_sim = (None, "Private work (CMS simulation)")


class CmsLabelsManager:
    def __init__(self, config):
        self.config = config

        self.show_labels = False
        if hasattr(self.config, "show_cms_labels"):
            self.show_labels = self.config.show_cms_labels

        cms_label = getattr(self.config, "cms_label", CmsLabel.paper)
        if not isinstance(cms_label, CmsLabel):
            raise TypeError("cms_label must be a CmsLabel enum value")
        if hasattr(self.config, "label_text") or hasattr(self.config, "extraText"):
            raise ValueError("Use cms_label with a CmsLabel enum value instead of free text")
        self.cmsText, self.extraText = cms_label.value
        
        self.cmsTextFont = 63

        self.extraTextFont = 53

        self.lumiTextSize = 0.6

        if hasattr(self.config, "lumi_label_offset"):
            self.lumiTextOffset = self.config.lumi_label_offset
        else:
            self.lumiTextOffset = -0.

        self.labelTextSize = 20
        self.cmsTextSize = 1.3 * self.labelTextSize
        self.cmsTextOffset = 0.1

        if config.show_ratio_plots:
            self.relPosX = 0.055
            self.relPosY = 0.04
        else:
            self.relPosX = 0.055
            self.relPosY = 0.04

        self.customLabelX = hasattr(self.config, "label_x")
        self.customLabelY = hasattr(self.config, "label_y")
        if self.customLabelX:
            self.relPosX = self.config.label_x
            
        if self.customLabelY:
            self.relPosY = self.config.label_y

        self.label_outside_axes = getattr(self.config, "label_outside_axes", False)

        if hasattr(self.config, "lumi_unit"):
            lumi_unit = self.config.lumi_unit
        else:
            lumi_unit = "fb"

        # get lumi and convert from pb to fb
        if hasattr(self.config, "lumi_label_value"):
            self.lumi = f"{self.config.lumi_label_value / 1000.0:.1f} {lumi_unit}^{{-1}}"
        else:
            self.lumi = ""

        if hasattr(self.config, "beam_label"):
            self.collision_energy = " (" + self.config.beam_label+")"
        else:
            self.collision_energy = " (13 TeV)"
            year = getattr(self.config, "year", "")
            if "2022" in year or "2023" in year:
                self.collision_energy = " (13.6 TeV)"

        self.drawLogo = False

    def drawLabels(self, pad):
        if not self.show_labels:
            return

        pad.cd()

        self.__setVariables(pad)
        self.__drawLumiText()

        if self.drawLogo:
            self.__drawLogo()
        else:
            self.__drawCmsText()
            self.__drawExtraCmsText()

        pad.cd()
        pad.Update()

    def __setVariables(self, pad):
        self.height = pad.GetWh() * pad.GetHNDC()
        self.width = pad.GetWw() * pad.GetWNDC()
        self.left = pad.GetLeftMargin()
        self.top = pad.GetTopMargin()
        self.right = pad.GetRightMargin()
        self.bottom = pad.GetBottomMargin()

    def __drawLumiText(self):
        lumiText = self.lumi + self.collision_energy
        if self.label_outside_axes:
            _, label_pos_y = self.__label_position()
        else:
            label_pos_y = 1-self.top + 10.0/self.height

        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextAngle(0)
        latex.SetTextColor(ROOT.kBlack)
        latex.SetTextFont(43)
        latex.SetTextAlign(31)

        latex.SetTextSize(self.labelTextSize)
        right_boundary = 1-self.right
        latex.DrawLatex(right_boundary, label_pos_y + self.lumiTextOffset * self.top, lumiText)

    def __drawLogo(self):
        posX_ = self.left + 0.045 * \
            (1-self.left-self.right) * self.width/self.height
        posY_ = 1-self.top - 0.045*(1-self.top-self.bottom)
        xl_0 = posX_
        yl_0 = posY_ - 0.15
        xl_1 = posX_ + 0.15 * self.height/self.width
        yl_1 = posY_
        CMS_logo = ROOT.TASImage("CMS-BW-label.png")
        pad_logo = ROOT.TPad("logo", "logo", xl_0, yl_0, xl_1, yl_1)
        pad_logo.Draw()
        pad_logo.cd()
        CMS_logo.Draw("X")
        pad_logo.Modified()

    def __drawCmsText(self):
        posX_, posY_ = self.__label_position()

        latex = ROOT.TLatex()
        latex.SetNDC()
        if self.cmsText is None:
            return

        latex.SetTextFont(self.cmsTextFont)
        latex.SetTextSize(self.cmsTextSize)
        latex.SetTextAlign(11 if self.label_outside_axes else 13)
        latex.DrawLatex(posX_, posY_, self.cmsText)

    def __drawExtraCmsText(self):
        if self.extraText is None:
            return

        posX_, posY_ = self.__label_position()
        if self.label_outside_axes and self.cmsText is not None:
            cms_width = self.__textWidth(
                self.cmsText, self.cmsTextFont, self.cmsTextSize)
            space_width = (
                self.__textWidth("CMS x", self.cmsTextFont, self.cmsTextSize)
                - self.__textWidth("CMSx", self.cmsTextFont, self.cmsTextSize))
            posX_ += (cms_width + space_width) / self.width

        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextFont(self.extraTextFont)
        latex.SetTextAlign(11 if self.label_outside_axes else 13)
        latex.SetTextSize(self.labelTextSize)
        extra_pos_y = posY_
        if not self.label_outside_axes and self.cmsText is not None:
            extra_pos_y -= (self.labelTextSize + 6.0)/self.height
        latex.DrawLatex(posX_, extra_pos_y, self.extraText)

    def __label_position(self):
        if self.label_outside_axes:
            return self.left, 1 - self.top + 10.0/self.height

        frame_width = self.width * (1 - self.left - self.right)
        frame_height = self.height * (1 - self.top - self.bottom)
        top_tick_length = ROOT.gStyle.GetTickLength("X") * frame_height
        left_tick_length = ROOT.gStyle.GetTickLength("Y") * frame_width
        tick_gap = 6.0
        axis_inset = max(top_tick_length, left_tick_length) + tick_gap
        default_x = self.left + axis_inset / self.width
        default_y = 1 - self.top - axis_inset / self.height
        label_x = (self.left + self.relPosX * (1-self.left-self.right)
                   if self.customLabelX else default_x)
        label_y = (1-self.top - self.relPosY * (1-self.top-self.bottom)
                   if self.customLabelY else default_y)
        return label_x, label_y

    @staticmethod
    def __textWidth(text, font, size):
        latex = ROOT.TLatex()
        latex.SetTextFont(font)
        latex.SetTextSize(size)
        latex.SetText(0, 0, text)
        width = ctypes.c_uint()
        height = ctypes.c_uint()
        latex.GetBoundingBox(width, height)
        return width.value

    def drawLabels2D(self, canvas):
        if self.cmsText is not None:
            latex = ROOT.TLatex()
            latex.SetTextFont(self.cmsTextFont)
            latex.SetTextSize(self.cmsTextSize)
            latex.SetTextAlign(13)
            latex.SetNDC()
            latex.DrawLatex(0.1, 0.99, self.cmsText)

        canvas.Update()
        cms_width = 0.0
        if self.cmsText is not None:
            cms_text_width = self.__textWidth(
                self.cmsText, self.cmsTextFont, self.cmsTextSize)
            space_width = (
                self.__textWidth("CMS x", self.cmsTextFont, self.cmsTextSize)
                - self.__textWidth("CMSx", self.cmsTextFont, self.cmsTextSize))
            cms_width = (cms_text_width + space_width) / canvas.GetWw()

        if self.extraText is not None:

            latex = ROOT.TLatex()
            latex.SetTextFont(self.extraTextFont)
            latex.SetTextAlign(13)
            latex.SetTextSize(self.labelTextSize)
            latex.SetNDC()
            posX_ = 0.1 if self.cmsText is None else 0.1 + cms_width
            posY_ = 0.99 if self.cmsText is None else 0.99 - 0.01
            latex.DrawLatex(posX_, posY_, self.extraText)
            

        lumiText = self.lumi + self.collision_energy
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextAngle(0)
        latex.SetTextColor(ROOT.kBlack)
        latex.SetTextFont(43)
        latex.SetTextAlign(31)
        latex.SetTextSize(self.labelTextSize)
        latex.DrawLatex(1-self.right, 1-self.top + 2*self.lumiTextOffset * self.top + 0.01, lumiText)
