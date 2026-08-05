#include "Profiler.hpp"

Profiler& Profiler::GetInstance() {
  static Profiler instance;
  return instance;
}
