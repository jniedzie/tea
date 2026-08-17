warn_messages = {}
error_messages = {}
fatal_messages = {}
root_warning_collector_installed = False


def info(message, end="\n"):
  print(message, end=end)


def warn(message):
  if message in warn_messages:
    warn_messages[message] += 1
    return

  warn_messages[message] = 1
  print(f"[first occurance]\033[1;33m{message}\033[0m")


def install_root_warning_collector():
  """Collect selected noisy ROOT warnings for the final logger summary."""
  import ROOT

  global root_warning_collector_installed
  if root_warning_collector_installed:
    return

  ROOT.gInterpreter.Declare(r"""
    #ifndef TEA_ROOT_WARNING_COLLECTOR
    #define TEA_ROOT_WARNING_COLLECTOR
    #include <cstring>
    #include "TError.h"

    namespace TeaRootWarnings {
      unsigned long empty_histogram_count = 0;
      unsigned long non_exact_rebin_count = 0;
      ErrorHandlerFunc_t previous_handler = nullptr;
      bool installed = false;

      void Handle(int level, Bool_t abort, const char *location,
                  const char *message) {
        if (location && message && std::strcmp(location, "TH1::TH1") == 0 &&
            std::strstr(message, "nbins is <=0")) {
          ++empty_histogram_count;
          return;
        }

        if (location && message && std::strstr(location, "::Rebin") &&
            std::strstr(message, "is not an exact divider of nbins=")) {
          ++non_exact_rebin_count;
          return;
        }

        if (previous_handler)
          previous_handler(level, abort, location, message);
        else
          DefaultErrorHandler(level, abort, location, message);
      }

      void Install() {
        if (installed)
          return;
        previous_handler = SetErrorHandler(Handle);
        installed = true;
      }

      unsigned long TakeEmptyHistogramCount() {
        const auto count = empty_histogram_count;
        empty_histogram_count = 0;
        return count;
      }

      unsigned long TakeNonExactRebinCount() {
        const auto count = non_exact_rebin_count;
        non_exact_rebin_count = 0;
        return count;
      }
    }
    #endif
  """)
  ROOT.TeaRootWarnings.Install()
  root_warning_collector_installed = True


def collect_root_warnings():
  if not root_warning_collector_installed:
    return

  import ROOT

  empty_count = int(ROOT.TeaRootWarnings.TakeEmptyHistogramCount())
  rebin_count = int(ROOT.TeaRootWarnings.TakeNonExactRebinCount())

  empty_message = "ROOT encountered an empty histogram (nbins <= 0; using one bin)."
  rebin_message = "ROOT rebinning group is not an exact divider of the histogram bins."
  warn_messages[empty_message] = warn_messages.get(empty_message, 0) + empty_count
  warn_messages[rebin_message] = warn_messages.get(rebin_message, 0) + rebin_count

  if warn_messages[empty_message] == 0:
    del warn_messages[empty_message]
  if warn_messages[rebin_message] == 0:
    del warn_messages[rebin_message]


def error(message):
  if message in error_messages:
    error_messages[message] += 1
    return

  error_messages[message] = 1

  print(f"[first occurance]\033[1;31m{message}\033[0m")


def fatal(message):
  if message in fatal_messages:
    fatal_messages[message] += 1
    return

  fatal_messages[message] = 1

  print("[first occurance]\033[1;35m" + message + "\033[0m")


def logger_print():
  collect_root_warnings()

  for message, count in warn_messages.items():
    print(f"[occured {count} times]\033[1;33m{message}\033[0m")

  for message, count in error_messages.items():
    print(f"[occured {count} times]\033[1;31m{message}\033[0m")

  for message, count in fatal_messages.items():
    print(f"[occured {count} times]\033[1;35m{message}\033[0m")
