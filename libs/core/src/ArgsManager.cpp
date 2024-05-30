#include "ArgsManager.hpp"
#include "Logger.hpp"

ArgsManager::ArgsManager(int argc, char **argv) {
    for (int i = 1; i < argc; i += 2) {
        std::string key = argv[i];
        if (key.size() < 2 || key[0] != '-' || key[1] != '-') {
            fatal() << "Invalid key: " << key << std::endl;
            exit(1);
        }
        key = key.substr(2);
        std::string value = argv[i + 1];
        args[key] = value;
    }
}
