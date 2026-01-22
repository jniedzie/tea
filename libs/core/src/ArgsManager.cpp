#include "ArgsManager.hpp"

#include "Logger.hpp"

using namespace std;

ArgsManager::ArgsManager(int argc, char** argv, std::vector<std::string> _requiredArgs, std::vector<std::string> _optionalArgs)
    : requiredArgs(_requiredArgs), optionalArgs(_optionalArgs) {
  for (int i = 1; i < argc; i += 2) {
    string key = argv[i];
    if (key.size() < 2 || key[0] != '-' || key[1] != '-') {
      fatal() << "Invalid key: " << key << endl;
      exit(1);
    }
    key = key.substr(2);
    string value = argv[i + 1];
    args[key] = value;
  }

  ValidateArgs();
}

void ArgsManager::ValidateArgs() {
  for (const auto& [key, value] : args) {
    if (std::find(requiredArgs.begin(), requiredArgs.end(), key) == requiredArgs.end() &&
        std::find(optionalArgs.begin(), optionalArgs.end(), key) == optionalArgs.end()) {
      fatal() << "ArgsManager -- Unknown argument provided: " << key << endl;
      exit(7);
    }
  }
  for (string requiredArg : requiredArgs) {
    if (args.count(requiredArg) == 0) {
      fatal() << "ArgsManager -- Required argument not provided: " << requiredArg << endl;
      exit(8);
    }
  }
}
