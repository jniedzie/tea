import re
import inspect


def get_year_from_samples(samples):
  frame = inspect.currentframe().f_back
  ns = frame.f_globals.copy()
  ns.update(frame.f_locals)

  source_name = None
  for name, obj in list(ns.items()):  # snapshot with list(...)
    if isinstance(obj, dict) and obj.keys() == samples:  # same keys view
      source_name = name
      break

  if not source_name:
    return None

  m = re.search(r'(\d{4}[A-Za-z]*)', source_name)
  return m.group(1) if m else None
