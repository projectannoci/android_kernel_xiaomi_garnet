#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
TOOLCHAIN_DIR=${TOOLCHAIN_DIR:-$PROJECT_DIR/toolchain}
export PATH="$TOOLCHAIN_DIR/bin:$PATH"
for cmd in clang ld.lld llvm-ar bc flex bison m4; do
  command -v "$cmd" >/dev/null || { echo "Missing dependency: $cmd" >&2; exit 1; }
done
mkdir -p "$PROJECT_DIR/out"
cp "$PROJECT_DIR/singularity.config" "$PROJECT_DIR/out/.config"
export KBUILD_BUILD_VERSION=1 KBUILD_BUILD_USER=ProjectNoci KBUILD_BUILD_HOST=Singularity
MAKE_ARGS=(
  -C "$PROJECT_DIR/kernel" O="$PROJECT_DIR/out"
  ARCH=arm64 LLVM=1 LLVM_IAS=1 CROSS_COMPILE=aarch64-linux-gnu-
  KSU_GIT_VERSION_VALID=1 KSU_GIT_VERSION=3418 KSU_GIT_TAG=v3.4.2
)
make "${MAKE_ARGS[@]}" olddefconfig
make "${MAKE_ARGS[@]}" -j"${JOBS:-6}" Image

python3 "$PROJECT_DIR/validation/check_vendor.py" "$PROJECT_DIR/out/vmlinux.symvers"
