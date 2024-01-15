#!/usr/bin/env bash

# Compile Atop C code, and create a basic log sample using the new executable.

# Ensure the whole script exits on failures.
set -e

# Force execution in docker to ensure reproducibility.
if [ ! -f /.dockerenv ]; then
  echo "Please run inside docker to isolate dependencies, prevent modifications to system, and ensure reproducibility. Aborting."
  echo "Example: docker run --rm -it -h fires-of-mount-doom1.theshire.co -v ~/Development/atoparser:/mnt/atoparser ubuntu:jammy bash -c '/mnt/atoparser/utils/build_atop.sh --atop v2.10.0'"
  exit 1
fi

# Pull out user args to modify default behavior.
atop_version=''
while [[ $# -gt 0 ]]; do
  case $1 in
    --atop)
      if [ -z "$2" ]; then echo "Must provide Atop version. Example: --atop v2.10.0"; exit 1; fi
      atop_version=$2
      shift
    ;;
  esac
  shift
done

if [ -z "${atop_version}" ]; then
  echo "No atop version specified. Please provide an Atop version as v<major>.<minor>.<maintenance> to continue. Example: --atop v2.10.0"
  exit 1
fi

# Turn on command echoing to show all commands as they run.
set -x

apt-get update
apt-get install -y \
  build-essential \
  git \
  libglib2.0-dev \
  libncursesw5-dev \
  zlib1g-dev

git clone https://github.com/Atoptool/atop
cd atop
git checkout -b ${atop_version} tags/${atop_version}
make atop
project_root="$(dirname "$(dirname "$(readlink -f "$0")")")"
mv ./atop "${project_root}/atop"
${project_root}/atop 1 5 -w "${project_root}/atop_${atop_version}.log"
echo "Atop ${atop_version} binary and sample log can be found on host at <mounted volume>/atop_${atop_version}.log"
