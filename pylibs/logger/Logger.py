warn_messages = {}
error_messages = {}
fatal_messages = {}

def info(message):
  print(message)
  
def warn(message):
  if message in warn_messages:
    warn_messages[message] += 1
    return
  
  warn_messages[message] = 1
  print(f"[first occurance]\033[1;33m{message}\033[0m")
  
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
  for message, count in warn_messages.items():
    print(f"[occured {count} times]\033[1;33m{message}\033[0m")
    
  for message, count in error_messages.items():
    print(f"[occured {count} times]\033[1;31m{message}\033[0m")
    
  for message, count in fatal_messages.items():
    print(f"[occured {count} times]\033[1;35m{message}\033[0m")
