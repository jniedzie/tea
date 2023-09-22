//  Profiler.hpp
//
//  Created by Jeremi Niedziela on 31/08/2023.

#ifndef Profiler_hpp
#define Profiler_hpp

#include "Helpers.hpp"

class Profiler {
 public:
  Profiler(const Profiler&) = delete;
  void operator=(const Profiler&) = delete;

  void Start(std::string name) { startTimes[name] = now(); }

  void Stop(std::string name) {
    if (!times.count(name)) times[name] = 0;
    times[name] += duration(startTimes[name], now());
  }

  void Print() {
    std::vector<std::pair<std::string, float>> sortedTimes(times.begin(), times.end());
    std::sort(sortedTimes.begin(), sortedTimes.end(), [](const auto& pair1, const auto& pair2) { return pair1.second > pair2.second; });
    for (auto& [name, t] : sortedTimes) info() << name << ": " << t << " (s)" << std::endl;
  }

  static Profiler& GetInstance() {
    static Profiler instance;
    return instance;
  }

 private:
  Profiler() {}

  std::map<std::string, float> times;
  std::map<std::string, std::chrono::time_point<std::chrono::steady_clock>> startTimes;

  bool compareByValue(const std::pair<std::string, float>& pair1, const std::pair<std::string, float>& pair2) {
    return pair1.second < pair2.second;
  }
};

#endif /* Profiler_hpp */
