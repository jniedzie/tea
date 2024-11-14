import ROOT


class CmsLabelsManager:
    def __init__(self, config):
        self.config = config

        self.show_labels = False
        if hasattr(self.config, "show_cms_labels"):
            self.show_labels = self.config.show_cms_labels

        self.cmsText = "CMS"
        if hasattr(self.config, "label_text"):
            self.cmsText = self.config.label_text
        
        self.cmsTextFont = 61

        self.extraText = None
        if hasattr(self.config, "extraText"):
            self.extraText = self.config.extraText
        self.extraTextFont = 52

        self.lumiTextSize = 0.6

        if hasattr(self.config, "lumi_label_offset"):
            self.lumiTextOffset = self.config.lumi_label_offset
        else:
            self.lumiTextOffset = -0.2

        self.cmsTextSize = 0.75
        self.cmsTextOffset = 0.1

        if config.show_ratio_plots:
            self.relPosX = 0.045
            self.relPosY = 0.035
            self.relExtraDY = 1.2
        else:
            self.relPosX = 0.045
            self.relPosY = 0.070
            self.relExtraDY = 1.2

        if hasattr(self.config, "label_y"):
            self.relPosY = self.config.label_y

        self.extraOverCmsTextSize = 0.76

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
        self.height = pad.GetWh()
        self.width = pad.GetWw()
        self.left = pad.GetLeftMargin()
        self.top = pad.GetTopMargin()
        self.right = pad.GetRightMargin()
        self.bottom = pad.GetBottomMargin()

    def __drawLumiText(self):
        lumiText = self.lumi + self.collision_energy

        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextAngle(0)
        latex.SetTextColor(ROOT.kBlack)
        latex.SetTextFont(42)
        latex.SetTextAlign(31)

        latex.SetTextSize(self.lumiTextSize*self.top)
        latex.DrawLatex(1-self.right, 1-self.top + self.lumiTextOffset * self.top, lumiText)

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

        posX_ = self.left + self.relPosX*(1-self.left-self.right)
        posY_ = 1-self.top - self.relPosY*(1-self.top-self.bottom)

        latex = ROOT.TLatex()
        latex.SetTextFont(self.cmsTextFont)
        latex.SetTextSize(self.cmsTextSize*self.top)
        latex.SetTextAlign(13)
        latex.DrawLatex(posX_, posY_, self.cmsText)

    def __drawExtraCmsText(self):
        if self.extraText is None:
            return

        posX_ = self.left + self.relPosX*(1-self.left-self.right)
        posY_ = 1-self.top - self.relPosY*(1-self.top-self.bottom)

        latex = ROOT.TLatex()
        latex.SetTextFont(self.extraTextFont)
        latex.SetTextAlign(13)
        extraTextSize = self.extraOverCmsTextSize * self.cmsTextSize
        latex.SetTextSize(extraTextSize*self.top)
        latex.DrawLatex(posX_, posY_ - self.relExtraDY *
                        self.cmsTextSize*self.top, self.extraText)
