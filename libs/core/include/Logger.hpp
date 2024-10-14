//  Logger.hpp
//
//  Created by Jeremi Niedziela on 07/08/2023.

#ifndef Logger_hpp
#define Logger_hpp

#include <stdexcept>

#include "Helpers.hpp"

class Logger {
 public:
  static Logger &GetInstance() {
    static Logger instance;
    return instance;
  }

  bool addWarning() {
    std::string warning = currentWarningStream.str();
    if (warnings.find(warning) == warnings.end()) {
      warnings[warning] = 1;
      return false;
    } else {
      warnings[warning]++;
      return true;
    }
    return false;
  }

  bool addError() {
    std::string error = currentErrorStream.str();
    if (errors.find(error) == errors.end()) {
      errors[error] = 1;
      return false;
    } else {
      errors[error]++;
      return true;
    }
    return false;
  }

  bool addFatal() {
    std::string fatal = currentFatalStream.str();
    if (fatals.find(fatal) == fatals.end()) {
      fatals[fatal] = 1;
      return false;
    } else {
      fatals[fatal]++;
      return true;
    }
    return false;
  }

  void Print() {
    for (auto &[warning, count] : warnings) {
      std::cout << "[occured " << count << " times] \033[1;33m" << warning << "\033[0m";
    }
    for (auto &[error, count] : errors) {
      std::cout << "[occured " << count << " times] \033[1;31m" << error << "\033[0m";
    }
    for (auto &[fatal, count] : fatals) {
      std::cout << "[occured " << count << " times] \033[1;35m" << fatal << "\033[0m";
    }
  }

  std::ostringstream currentWarningStream, currentErrorStream, currentFatalStream;

  Logger(Logger const &) = delete;
  Logger &operator=(Logger const &) = delete;

 private:
  Logger(){};
  std::map<std::string, int> warnings, errors, fatals;
};

struct info {
  template <class T>
  info &operator<<(const T &v) {
    std::cout << v;
    return *this;
  }
  info &operator<<(std::ostream &(*os)(std::ostream &)) {
    std::cout << os;
    return *this;
  }
};

struct warn {
  template <class T>
  warn &operator<<(const T &v) {
    auto &logger = Logger::GetInstance();
    logger.currentWarningStream << v;
    return *this;
  }
  warn &operator<<(std::ostream &(*os)(std::ostream &)) {
    auto &logger = Logger::GetInstance();
    logger.currentWarningStream << os;
    if (!logger.addWarning()) {
      std::cout << "[first occurence] \033[1;33m" << logger.currentWarningStream.str() << "\033[0m";
    }
    logger.currentWarningStream.str("");
    return *this;
  }
};

struct error {
  template <class T>
  error &operator<<(const T &v) {
    auto &logger = Logger::GetInstance();
    logger.currentErrorStream << v;
    return *this;
  }
  error &operator<<(std::ostream &(*os)(std::ostream &)) {
    auto &logger = Logger::GetInstance();
    logger.currentErrorStream << os;
    if (!logger.addError()) {
      std::cout << "[first occurence] \033[1;31m" << logger.currentErrorStream.str() << "\033[0m";
    }
    logger.currentErrorStream.str("");
    return *this;
  }
};

struct fatal {
  const char *file;
  const char *function;
  int line;

  fatal(const char *file = __builtin_FILE(), const char *function = __builtin_FUNCTION(), int line = __builtin_LINE())
      : file(file), function(function), line(line) {}

  template <class T>
  fatal &operator<<(const T &v) {
    auto &logger = Logger::GetInstance();
    logger.currentFatalStream << v;
    return *this;
  }

  fatal &operator<<(std::ostream &(*os)(std::ostream &)) {
    std::string errorDetails = "The problem likely originates from:";
    errorDetails += "\nFile: " + std::string(file);
    errorDetails += "\nFunction: " + std::string(function);
    errorDetails += "\nLine: " + std::to_string(line);

    auto &logger = Logger::GetInstance();
    logger.currentFatalStream << os << "\n" << errorDetails;

    if(!logger.addFatal()) {
      std::cout << "[first occurrence] \033[1;35m" << logger.currentFatalStream.str() << "\033[0m" << std::endl;
    }
    logger.currentFatalStream.str("");

    return *this;
  }
};

class Exception : public std::exception {
 public:
  Exception(const char *message) { message_ = "\033[1;35m" + (std::string)message + "\033[0m"; }
  virtual const char *what() const throw() { return message_.c_str(); }

 private:
  std::string message_;
};

#endif /* Logger_hpp */
