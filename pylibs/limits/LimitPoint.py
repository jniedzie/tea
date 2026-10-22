"""Validated, analysis-independent limit records and explicit input adapters."""

from dataclasses import dataclass, field, replace, asdict
import ast
import json
import math
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional

QUANTILES = (0.025, 0.16, 0.5, 0.84, 0.975)
STATUSES = {"ok", "unavailable", "failed", "no_sensitivity"}


def finite_number(value: Any, label: str, positive: bool = False) -> float:
  if isinstance(value, bool):
    raise ValueError(f"{label} must be numeric")
  number = float(value)
  if not math.isfinite(number) or (positive and number <= 0):
    raise ValueError(f"{label} must be finite{' and positive' if positive else ''}")
  return number


@dataclass(frozen=True)
class LimitPoint:
  id: str
  x: float
  expected: Mapping[float, float] = field(default_factory=dict)
  observed: Optional[float] = None
  quantity: str = "r"
  parameters: Mapping[str, Any] = field(default_factory=dict)
  metadata: Mapping[str, Any] = field(default_factory=dict)
  nominal_cross_section: Optional[float] = None
  status: str = "ok"
  message: str = ""

  def __post_init__(self) -> None:
    if not isinstance(self.id, str) or not self.id:
      raise ValueError("A nonempty point id is required")
    object.__setattr__(self, "x", finite_number(self.x, f"{self.id}: x"))
    aliases = {"succeeded": "ok", "no-sensitivity": "no_sensitivity"}
    object.__setattr__(self, "status", aliases.get(self.status, self.status))
    if self.quantity not in ("r", "cross_section"):
      raise ValueError("Point quantity must be r or cross_section")
    if self.status not in STATUSES:
      raise ValueError(f"{self.id}: unknown status {self.status!r}")
    expected = {
      float(key): finite_number(value, f"{self.id}: quantile {key}", True) for key, value in self.expected.items()
    }
    if self.status == "ok" or expected:
      if set(expected) != set(QUANTILES) or len(self.expected) != len(QUANTILES):
        raise ValueError(f"{self.id}: expected must label exactly {QUANTILES}")
      values = [expected[q] for q in QUANTILES]
      if values != sorted(values):
        raise ValueError(f"{self.id}: expected quantiles are unordered")
    object.__setattr__(self, "expected", expected)
    if self.observed is not None:
      object.__setattr__(self, "observed", finite_number(self.observed, f"{self.id}: observed", True))
    if self.nominal_cross_section is not None:
      object.__setattr__(
        self,
        "nominal_cross_section",
        finite_number(self.nominal_cross_section, f"{self.id}: nominal cross section", True),
      )


def validate_collection(points: Iterable[LimitPoint]) -> list:
  points = list(points)
  ids = [point.id for point in points]
  if len(ids) != len(set(ids)):
    raise ValueError("Duplicate point ids; preserve the complete model identity")
  return points


def scale_point(point: LimitPoint, quantity: str = "r", constant_scale: Optional[float] = None) -> LimitPoint:
  if quantity not in ("r", "cross_section"):
    raise ValueError("quantity must be 'r' or 'cross_section'")
  if point.status != "ok" or quantity == point.quantity:
    return point
  factor = constant_scale if constant_scale is not None else point.nominal_cross_section
  if factor is None:
    raise ValueError(f"{point.id}: nominal_cross_section is required for conversion")
  factor = finite_number(factor, "cross section scale", True)
  if quantity == "r":
    factor = 1 / factor
  return replace(
    point,
    quantity=quantity,
    expected={q: value * factor for q, value in point.expected.items()},
    observed=None if point.observed is None else point.observed * factor,
  )


def read_points(path: Path, point_adapter: Optional[Callable] = None) -> list:
  """Read JSON records, or old ``name: [obs, five expected]`` text with an explicit adapter.

  The adapter receives the complete legacy name and returns id/x/parameters/metadata/nominal fields.
  Five positional values mean expected-only; six mean observed then expected. New JSON is always labeled.
  """
  path = Path(path)
  if path.suffix == ".json":
    document = json.loads(path.read_text())
    records = document["points"] if isinstance(document, dict) else document
    return validate_collection(LimitPoint(**record) for record in records)
  if point_adapter is None:
    raise ValueError("Legacy text requires config.point_adapter(name); no signal-name inference is performed")
  points = []
  for number, line in enumerate(path.read_text().splitlines(), 1):
    if not line.strip():
      continue
    name, separator, raw = line.partition(":")
    if not separator:
      raise ValueError(f"{path}:{number}: missing ':'")
    values = ast.literal_eval(raw.strip())
    if not isinstance(values, (list, tuple)) or len(values) not in (5, 6):
      raise ValueError(f"{path}:{number}: expected five quantiles, optionally preceded by observed")
    identity = {"id": name.strip(), **point_adapter(name.strip())}
    points.append(
      LimitPoint(
        **identity, expected=dict(zip(QUANTILES, values[-5:])), observed=values[0] if len(values) == 6 else None
      )
    )
  return validate_collection(points)


def write_points(path: Path, points: Iterable[LimitPoint]) -> None:
  path = Path(path)
  path.parent.mkdir(parents=True, exist_ok=True)
  records = [asdict(point) for point in validate_collection(points)]
  path.write_text(json.dumps({"schema_version": 1, "points": records}, indent=2, allow_nan=False) + "\n")
