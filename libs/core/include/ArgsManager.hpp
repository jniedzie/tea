#pragma once

#include "Helpers.hpp"
#include "Multitype.hpp"

class ArgsManager {
 public:
  ArgsManager(int argc, char** argv, std::vector<std::string> _requiredArgs, std::vector<std::string> _optionalArgs);
  ~ArgsManager() {}

  inline std::optional<std::string> GetString(std::string key) {
    if (args.count(key) == 0) return std::nullopt;
    return args[key];
  }

  inline std::optional<int> GetInt(std::string key) {
    if (args.count(key) == 0) return std::nullopt;
    return std::stoi(args[key]);
  }

  inline std::optional<float> GetFloat(std::string key) {
    if (args.count(key) == 0) return std::nullopt;
    return std::stof(args[key]);
  }

  inline std::optional<bool> GetBool(std::string key) {
    if (args.count(key) == 0) return std::nullopt;
    return args[key] == "True";
  }

 private:
  void ValidateArgs();

  std::vector<std::string> requiredArgs, optionalArgs;
  std::map<std::string, std::string> args;
};
