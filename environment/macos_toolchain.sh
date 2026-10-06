#!/bin/bash

# Sourced by build.sh after activating the pinned environment.
tea_macos_use_sdk() {
  local sdk_environment
  # Shell profiles sometimes inject SDK headers/libraries into these paths.
  # Keep them consistent with the SDK selected for this build.
  sdk_environment="$("${CONDA_PREFIX}/bin/python3" - "$1" <<'PY'
import os
import re
import shlex
import sys

sdk = sys.argv[1]
def replace_sdk(value):
    return re.sub(r"/.*?\.sdk(?=/|$)", lambda match: sdk, value)

for key in ("CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS"):
    if key in os.environ:
        words = shlex.split(os.environ[key])
        value = shlex.join([replace_sdk(word) for word in words])
        print(f"export {key}={shlex.quote(value)}")
for key in ("CPATH", "C_INCLUDE_PATH", "CPLUS_INCLUDE_PATH"):
    if key in os.environ:
        value = ":".join(replace_sdk(path) for path in os.environ[key].split(":"))
        print(f"export {key}={shlex.quote(value)}")
print(f"export SDKROOT={shlex.quote(sdk)}")
PY
  )" || return 1
  eval "${sdk_environment}"
}

tea_macos_select_toolchain() {
  local check_dir requested_sdk sdk candidate apple_cc apple_cxx
  local -a sdk_candidates
  check_dir="$1"
  requested_sdk="${2:-}"
  mkdir -p "${check_dir}"
  cat > "${check_dir}/CMakeLists.txt" <<'CMAKE'
cmake_minimum_required(VERSION 3.14)
project(tea_toolchain_check LANGUAGES C CXX)
add_executable(check_c main.c)
add_executable(check_cxx main.cpp)
set_property(TARGET check_cxx PROPERTY CXX_STANDARD 20)
CMAKE
  printf '#include <stdio.h>\nint main(void) { puts("tea"); return 0; }\n' > "${check_dir}/main.c"
  printf '#include <iostream>\nint main() { std::cout << "tea\\n"; }\n' > "${check_dir}/main.cpp"

  sdk_candidates=()
  if [[ -n "${requested_sdk}" ]]; then
    sdk_candidates=("${requested_sdk}")
  else
    sdk="$(xcrun --sdk macosx --show-sdk-path 2>/dev/null || true)"
    [[ -z "${sdk}" ]] || sdk_candidates+=("${sdk}")
    sdk_candidates+=(/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk)
    if [[ -d /Library/Developer/CommandLineTools/SDKs ]]; then
      while IFS= read -r sdk; do
        sdk_candidates+=("${sdk}")
      done < <(find /Library/Developer/CommandLineTools/SDKs -maxdepth 1 -type d -name 'MacOSX*.sdk' | sort -r)
    fi
  fi

  TEA_MACOS_SDK=""
  TEA_MACOS_CC="$(command -v "${CC}")" || return 1
  TEA_MACOS_CXX="$(command -v "${CXX}")" || return 1
  for candidate in "${sdk_candidates[@]}"; do
    [[ -f "${candidate}/usr/include/stdio.h" && -f "${candidate}/usr/lib/libSystem.tbd" ]] || continue
    sdk="$(cd "${candidate}" && pwd -P)"
    tea_macos_use_sdk "${sdk}" || return 1
    # Remember a valid SDK for the Apple compiler fallback.
    [[ -n "${TEA_MACOS_SDK}" ]] || TEA_MACOS_SDK="${sdk}"
    rm -rf "${check_dir}/build"
    if cmake -S "${check_dir}" -B "${check_dir}/build" \
        "-DCMAKE_C_COMPILER=${TEA_MACOS_CC}" \
        "-DCMAKE_CXX_COMPILER=${TEA_MACOS_CXX}" \
        "-DCMAKE_OSX_SYSROOT=${sdk}" > "${check_dir}/pinned.log" 2>&1 &&
        cmake --build "${check_dir}/build" >> "${check_dir}/pinned.log" 2>&1; then
      TEA_MACOS_SDK="${sdk}"
      echo "tea: using pinned compilers with macOS SDK ${sdk}"
      return 0
    fi
  done

  if [[ -z "${TEA_MACOS_SDK}" ]]; then
    echo "tea: no usable macOS SDK found. Install Apple's standalone Command Line Tools with:" >&2
    echo "  xcode-select --install" >&2
    echo "Or set SDKROOT to an existing SDK directory. Full Xcode is not required." >&2
    return 1
  fi

  apple_cc="$(xcrun --find clang 2>/dev/null || true)"
  apple_cxx="$(xcrun --find clang++ 2>/dev/null || true)"
  if [[ -x "${apple_cc}" && -x "${apple_cxx}" ]]; then
    tea_macos_use_sdk "${TEA_MACOS_SDK}" || return 1
    rm -rf "${check_dir}/build"
    if cmake -S "${check_dir}" -B "${check_dir}/build" \
        "-DCMAKE_C_COMPILER=${apple_cc}" \
        "-DCMAKE_CXX_COMPILER=${apple_cxx}" \
        "-DCMAKE_OSX_SYSROOT=${TEA_MACOS_SDK}" > "${check_dir}/apple.log" 2>&1 &&
        cmake --build "${check_dir}/build" >> "${check_dir}/apple.log" 2>&1; then
      TEA_MACOS_CC="${apple_cc}"
      TEA_MACOS_CXX="${apple_cxx}"
      echo "tea: pinned tools cannot use the installed SDK; using Apple compilers with ${TEA_MACOS_SDK}"
      return 0
    fi
  fi
  echo "tea: cannot compile and link with the available macOS SDK. See ${check_dir}/*.log." >&2
  echo "Set SDKROOT to a compatible SDK, or install/update Apple's Command Line Tools." >&2
  return 1
}
