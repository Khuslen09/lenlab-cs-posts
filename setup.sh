#!/usr/bin/env bash
# Installs card fonts locally and prints the --fonts path for build.py
set -e
FONTS="${FONTS_DIR:-$HOME/.lenlab-fonts}"
mkdir -p "$FONTS" && cd "$FONTS"
[ -f package.json ] || echo '{"name":"lenlab-fonts","private":true}' > package.json
npm i --silent pretendard @fontsource/jetbrains-mono @fontsource/libre-baskerville >/dev/null 2>&1
python3 -c "import playwright" 2>/dev/null || pip install --break-system-packages -q playwright
echo "$FONTS/node_modules"
