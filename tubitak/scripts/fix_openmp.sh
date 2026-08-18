#!/usr/bin/env bash
#
# fix_openmp.sh — point PyTorch's bundled OpenMP runtime at the conda one.
#
# Symptom this fixes:
#   OMP: Error #15: Initializing libomp.dylib, but found libomp.dylib already
#   initialized.  ...raised by a bare `import torch`, aborting the process.
#
# Cause: conda-forge packages (numpy, rasterio, ...) link against conda's
# llvm-openmp, while the pip torch wheel ships its own libomp.dylib. Two OpenMP
# runtimes in one process is unsupported.
#
# Fix: replace torch's bundled copy with a symlink to the conda one, so exactly
# ONE runtime is loaded. We deliberately do NOT set KMP_DUPLICATE_LIB_OK=TRUE:
# that merely silences the guard and lets both runtimes coexist, which risks
# silently incorrect numerics.
#
# Idempotent: safe to run repeatedly. Re-run after ANY torch reinstall/upgrade,
# which restores the bundled copy and reintroduces the crash.
#
# Usage:  conda activate gencp && bash tubitak/scripts/fix_openmp.sh
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "[fix_openmp] $*"; }

# ---- locate the conda environment -------------------------------------------
ENV_PREFIX="${CONDA_PREFIX:-}"
if [[ -z "$ENV_PREFIX" ]]; then
  command -v conda >/dev/null 2>&1 || die "conda not on PATH and CONDA_PREFIX unset. Activate the env first: conda activate gencp"
  ENV_PREFIX="$(conda info --base)/envs/gencp"
  info "CONDA_PREFIX unset; falling back to $ENV_PREFIX"
fi
[[ -d "$ENV_PREFIX" ]] || die "conda environment not found: $ENV_PREFIX"

case "$(basename "$ENV_PREFIX")" in
  gencp) ;;
  *) info "WARNING: active environment is '$(basename "$ENV_PREFIX")', not 'gencp'. Continuing against it." ;;
esac

# ---- locate both libomp copies ----------------------------------------------
CONDA_OMP="$ENV_PREFIX/lib/libomp.dylib"
[[ -f "$CONDA_OMP" ]] || die "conda libomp not found at $CONDA_OMP (expected from the llvm-openmp package)"

# Resolve site-packages via sysconfig rather than importing torch: when this bug
# is active `import torch` aborts the interpreter, so it cannot be relied on here.
SITE_PACKAGES="$("$ENV_PREFIX/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])' 2>/dev/null || true)"
[[ -n "$SITE_PACKAGES" && -d "$SITE_PACKAGES" ]] || die "could not determine site-packages for $ENV_PREFIX/bin/python"

TORCH_LIB_DIR="$SITE_PACKAGES/torch/lib"
[[ -d "$TORCH_LIB_DIR" ]] || die "torch lib directory not found at $TORCH_LIB_DIR. Is torch installed in $ENV_PREFIX?"

TORCH_OMP="$TORCH_LIB_DIR/libomp.dylib"

info "conda libomp : $CONDA_OMP"
info "torch libomp : $TORCH_OMP"

# ---- already fixed? ----------------------------------------------------------
if [[ -L "$TORCH_OMP" ]]; then
  CURRENT_TARGET="$(readlink "$TORCH_OMP")"
  if [[ "$CURRENT_TARGET" == "$CONDA_OMP" ]]; then
    info "already symlinked to the conda runtime — nothing to do."
    exit 0
  fi
  die "torch libomp is a symlink to an unexpected target: $CURRENT_TARGET
     Refusing to touch it. Inspect manually, then re-run."
fi

[[ -e "$TORCH_OMP" ]] || die "expected a bundled libomp at $TORCH_OMP but found nothing.
     torch's layout may have changed; do not apply this fix blindly."

# ---- back up, then link ------------------------------------------------------
BACKUP="$TORCH_OMP.bak"
if [[ -e "$BACKUP" ]]; then
  BACKUP="$TORCH_OMP.bak.$(date +%Y%m%d%H%M%S)"
  info "an earlier backup exists; using $BACKUP"
fi

mv "$TORCH_OMP" "$BACKUP" || die "could not back up $TORCH_OMP (permissions?)"
ln -s "$CONDA_OMP" "$TORCH_OMP" || die "could not create symlink $TORCH_OMP -> $CONDA_OMP"

info "backed up bundled copy to $BACKUP"
info "linked $TORCH_OMP -> $CONDA_OMP"

# ---- verify ------------------------------------------------------------------
if "$ENV_PREFIX/bin/python" -c "import torch; print('[fix_openmp] verified: import torch OK, version', torch.__version__)"; then
  exit 0
fi
die "torch still fails to import after linking. Restore with:
     mv '$BACKUP' '$TORCH_OMP'"
