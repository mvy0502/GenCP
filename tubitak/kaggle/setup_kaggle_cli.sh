#!/bin/bash
# Kaggle CLI in a dedicated virtualenv. Deliberately NOT the `gencp` conda env: the Kaggle
# client pulls in its own http/urllib3/certifi stack and the gencp dependency graph is
# load-bearing for the rest of the project.
#
# Prerequisite (browser step, do it first):
#   kaggle.com -> Settings -> API -> Create New Token  => downloads kaggle.json
#
# Usage:
#   bash tubitak/kaggle/setup_kaggle_cli.sh [path/to/kaggle.json]     # default: ~/Downloads/kaggle.json
#
# Afterwards, in any shell:
#   ~/.venvs/kaggle/bin/kaggle <command>
set -euo pipefail

VENV="$HOME/.venvs/kaggle"
TOKEN_SRC="${1:-$HOME/Downloads/kaggle.json}"
TOKEN_DST="$HOME/.kaggle/kaggle.json"

if [ ! -f "$TOKEN_SRC" ]; then
  echo "error: no token at $TOKEN_SRC"
  echo "       kaggle.com -> Settings -> API -> Create New Token, then re-run."
  exit 1
fi

echo "==> virtualenv at $VENV"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet kaggle

echo "==> installing token at $TOKEN_DST (mode 600)"
mkdir -p "$HOME/.kaggle"
install -m 600 "$TOKEN_SRC" "$TOKEN_DST"
chmod 600 "$TOKEN_DST"

echo "==> verifying (cheap authenticated call, no upload)"
"$VENV/bin/kaggle" datasets list --mine
echo
"$VENV/bin/kaggle" kernels list --mine
echo
echo "OK. The client is at $VENV/bin/kaggle"
echo "Delete $TOKEN_SRC once you have confirmed the above worked."
