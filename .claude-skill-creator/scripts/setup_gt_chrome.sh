#!/usr/bin/env bash
# setup_gt_chrome.sh
#
# Makes sure a headless Chrome/Chromium binary is available so that
# great_tables' GT.gtsave() can render PNG/PDF output via the `nokap` package.
# gtsave() needs a real Chrome/Chromium executable on the system -- it does not
# ship or download one itself. This script finds one, and if none exists (common
# on fresh sandboxes/containers with no system browser and no root access), it
# provisions one using `pip install playwright` + `playwright install chromium`
# (both work without root) and patches around any missing shared libraries.
#
# Usage: source this script (not just execute it) so the exported env vars
# stick around for the Python process that calls gtsave():
#
#   source scripts/setup_gt_chrome.sh
#   python3 my_table_script.py
#
# Safe to re-run. If a working browser is already configured, it's a no-op.

GT_CACHE_DIR="${HOME}/.cache/gt-skill-chrome"
GT_LIB_DIR="${GT_CACHE_DIR}/libs"
mkdir -p "$GT_LIB_DIR"

_gt_try_launch() {
  # Returns 0 if the given chrome binary can launch headlessly.
  local bin="$1"
  [ -x "$bin" ] || command -v "$bin" >/dev/null 2>&1 || return 1
  LD_LIBRARY_PATH="${GT_LIB_DIR}:${LD_LIBRARY_PATH:-}" "$bin" \
    --headless --disable-gpu --no-sandbox --dump-dom about:blank \
    > "${GT_CACHE_DIR}/last_launch.log" 2>&1
}

_gt_find_working_chrome() {
  local candidates=(
    "${CHROME_PATH:-}"
    "$(command -v google-chrome-stable 2>/dev/null)"
    "$(command -v google-chrome 2>/dev/null)"
    "$(command -v chromium 2>/dev/null)"
    "$(command -v chromium-browser 2>/dev/null)"
    "${HOME}"/.cache/ms-playwright/chromium-*/chrome-linux/chrome
  )
  for c in "${candidates[@]}"; do
    [ -n "$c" ] || continue
    for expanded in $c; do
      [ -e "$expanded" ] || continue
      if _gt_try_launch "$expanded"; then
        echo "$expanded"
        return 0
      fi
    done
  done
  return 1
}

# 1) Is a working browser already reachable?
FOUND="$(_gt_find_working_chrome)"

if [ -z "$FOUND" ]; then
  echo "[gt-setup] No working Chrome/Chromium found -- provisioning one via Playwright (no root needed)..." >&2

  if ! python3 -c "import playwright" 2>/dev/null; then
    pip install playwright --break-system-packages -q 2>&1 | tail -5
  fi
  python3 -m playwright install chromium > "${GT_CACHE_DIR}/install.log" 2>&1

  FOUND="$(_gt_find_working_chrome)"
fi

# 2) If it still won't launch, it's almost always missing shared libraries
#    (libXdamage, libnss3, etc.) that normally come from `playwright install-deps`,
#    which requires root. Work around this by downloading just the .deb files
#    (apt-get download needs no root/lock) and extracting them locally.
if [ -z "$FOUND" ]; then
  echo "[gt-setup] Chrome exists but won't launch -- fetching missing shared libraries locally..." >&2
  PKGS="libxdamage1 libxfixes3 libxcomposite1 libxrandr2 libxkbcommon0 libxss1 \
        libgbm1 libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
        libnss3 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libglib2.0-0"
  ( cd "$GT_CACHE_DIR" && apt-get download $PKGS > download.log 2>&1 )
  for deb in "$GT_CACHE_DIR"/*.deb; do
    [ -e "$deb" ] || continue
    dpkg-deb -x "$deb" "$GT_CACHE_DIR/extracted" 2>/dev/null
  done
  # Shared libs can land under lib/<arch> or usr/lib/<arch> depending on the package.
  find "$GT_CACHE_DIR/extracted" -name '*.so*' -exec dirname {} \; 2>/dev/null | sort -u > "$GT_CACHE_DIR/libdirs.txt"
  while IFS= read -r d; do
    ln -sf "$d"/*.so* "$GT_LIB_DIR"/ 2>/dev/null
  done < "$GT_CACHE_DIR/libdirs.txt"

  FOUND="$(_gt_find_working_chrome)"
fi

if [ -z "$FOUND" ]; then
  echo "[gt-setup] FAILED to provision a working headless Chrome. gtsave() will not work." >&2
  echo "[gt-setup] Check ${GT_CACHE_DIR}/last_launch.log and ${GT_CACHE_DIR}/install.log for details." >&2
  return 1 2>/dev/null || exit 1
fi

export CHROME_PATH="$FOUND"
export LD_LIBRARY_PATH="${GT_LIB_DIR}:${LD_LIBRARY_PATH:-}"
echo "[gt-setup] Ready. CHROME_PATH=${CHROME_PATH}" >&2