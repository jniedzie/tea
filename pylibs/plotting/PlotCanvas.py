"""Canvas export shared by histogram and graph plotters."""

from array import array
import os
from typing import Any


def save_canvas(canvas: Any, path: str) -> None:
  import ROOT
  from ROOT import gStyle

  path = os.fspath(path)
  output_directory = os.path.dirname(path)
  if output_directory:
    os.makedirs(output_directory, exist_ok=True)
  # Batch exports can retain a cached frame after late legends/labels.
  # Repaint the pads as well as the canvas before writing the final figure.
  for primitive in canvas.GetListOfPrimitives():
    if primitive.InheritsFrom("TPad"):
      primitive.Modified()
  canvas.Modified()
  canvas.Update()
  original_paper_width, original_paper_height = array("f", [0.0]), array("f", [0.0])
  gStyle.GetPaperSize(original_paper_width, original_paper_height)
  if os.path.splitext(path)[1].lower() == ".pdf":
    # Fit the drawable canvas onto ROOT's A4 page without changing its aspect.
    width, height = canvas.GetWw(), canvas.GetWh()
    paper_width, paper_height = (28.0, 20.0) if width >= height else (20.0, 28.0)
    scale = min(paper_width / width, paper_height / height)
    gStyle.SetPaperSize(width * scale, height * scale)
  original_error_level = ROOT.gErrorIgnoreLevel
  ROOT.gErrorIgnoreLevel = ROOT.kError
  try:
    canvas.SaveAs(path)
  finally:
    ROOT.gErrorIgnoreLevel = original_error_level
    gStyle.SetPaperSize(original_paper_width[0], original_paper_height[0])
