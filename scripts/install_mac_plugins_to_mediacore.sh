#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGE=""
SOURCE_DIR=""
MEDIA_CORE="$HOME/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore"
BACKUP_ROOT="$ROOT/handoff/mac_plugin_backups"
ALLOW_AE_RUNNING=0
DRY_RUN=0
AUDIT_ONLY=0

plugins=(
  ColorKeep
  OLMBlur
  OLMColorKey
  OLMDirectionalBlur
  OLMRadialBlur
  OLMKiraKira
  OLMToonDilate
  OLMDistanceGradation
  OLMSmoother
  OLMSmoother2
)

usage() {
  cat <<'EOF'
Usage:
  scripts/install_mac_plugins_to_mediacore.sh --package path/to/olm_mac_plugins_Debug_clean.zip
  scripts/install_mac_plugins_to_mediacore.sh --source-dir path/to/OLM_Mac_Plugins_Debug

Safely installs the expected OLM macOS AE plug-ins into MediaCore:
- requires After Effects to be closed unless --allow-ae-running is passed
- moves existing expected OLM bundles under MediaCore into a timestamped backup
- installs only the bundles from the package/source directory
- verifies exactly one installed bundle per expected OLM plug-in
- verifies installed binary SHA-256 matches the source bundle

Options:
  --package ZIP          Mac plug-in package zip from package_mac_plugins.sh
  --source-dir DIR       Directory containing packaged *.plugin bundles
  --media-core DIR       Override MediaCore target
  --backup-root DIR      Override backup root (default: handoff/mac_plugin_backups)
  --allow-ae-running     Do not fail if an After Effects process is detected
  --dry-run              Print planned actions without moving/copying
  --audit-only           Only list expected OLM bundles currently visible under MediaCore
  -h, --help             Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --package)
      PACKAGE="$2"
      shift 2
      ;;
    --source-dir)
      SOURCE_DIR="$2"
      shift 2
      ;;
    --media-core)
      MEDIA_CORE="$2"
      shift 2
      ;;
    --backup-root)
      BACKUP_ROOT="$2"
      shift 2
      ;;
    --allow-ae-running)
      ALLOW_AE_RUNNING=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --audit-only)
      AUDIT_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -n "$PACKAGE" && -n "$SOURCE_DIR" ]]; then
  echo "use either --package or --source-dir, not both" >&2
  exit 2
fi
if [[ -z "$PACKAGE" && -z "$SOURCE_DIR" && "$AUDIT_ONLY" -eq 0 ]]; then
  echo "missing --package or --source-dir" >&2
  usage >&2
  exit 2
fi

find_installed_bundles() {
  local plugin="$1"
  /usr/bin/find "$MEDIA_CORE" -maxdepth 6 -type d -name "$plugin.plugin" -print 2>/dev/null || true
}

if [[ "$AUDIT_ONLY" -eq 1 ]]; then
  echo "target: $MEDIA_CORE"
  if [[ ! -d "$MEDIA_CORE" ]]; then
    echo "[MISS] MediaCore directory not found"
    exit 1
  fi
  status=0
  for plugin in "${plugins[@]}"; do
    installed=()
    while IFS= read -r bundle; do
      [[ -z "$bundle" ]] && continue
      installed+=("$bundle")
    done < <(find_installed_bundles "$plugin")
    count="${#installed[@]}"
    if [[ "$count" -eq 0 ]]; then
      echo "[MISS] $plugin.plugin"
      status=1
    elif [[ "$count" -eq 1 ]]; then
      echo "[OK] $plugin.plugin"
      printf '  %s\n' "${installed[@]}"
    else
      echo "[DUPLICATE] $plugin.plugin count=$count"
      printf '  %s\n' "${installed[@]}"
      status=1
    fi
  done
  exit "$status"
fi

if [[ "$ALLOW_AE_RUNNING" -eq 0 ]] && pgrep -fl "After Effects" >/dev/null 2>&1; then
  echo "[FAIL] After Effects appears to be running. Quit AE first or pass --allow-ae-running." >&2
  pgrep -fl "After Effects" >&2 || true
  exit 1
fi

tmp_dir=""
cleanup() {
  if [[ -n "$tmp_dir" ]]; then
    rm -rf "$tmp_dir"
  fi
}
trap cleanup EXIT

if [[ -n "$PACKAGE" ]]; then
  if [[ ! -f "$PACKAGE" ]]; then
    echo "[MISS] package not found: $PACKAGE" >&2
    exit 1
  fi
  tmp_dir="$(mktemp -d "${TMPDIR:-/tmp}/olm_mac_install.XXXXXX")"
  python3 -m zipfile -e "$PACKAGE" "$tmp_dir"
  SOURCE_DIR="$tmp_dir"
fi

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "[MISS] source directory not found: $SOURCE_DIR" >&2
  exit 1
fi

find_source_bundle() {
  local plugin="$1"
  /usr/bin/find "$SOURCE_DIR" -maxdepth 3 -type d -name "$plugin.plugin" -print -quit
}

if [[ ! -d "$MEDIA_CORE" && "$DRY_RUN" -eq 0 ]]; then
  mkdir -p "$MEDIA_CORE"
fi

for plugin in "${plugins[@]}"; do
  bundle="$(find_source_bundle "$plugin")"
  if [[ -z "$bundle" ]]; then
    echo "[MISS] $plugin.plugin not found under source: $SOURCE_DIR" >&2
    exit 1
  fi
  binary="$bundle/Contents/MacOS/$plugin"
  if [[ ! -f "$binary" ]]; then
    echo "[MISS] $plugin binary missing in source bundle: $binary" >&2
    exit 1
  fi
done

stamp="$(date +%Y%m%d_%H%M%S)"
backup_dir="$BACKUP_ROOT/mediacore_${stamp}"

echo "source: $SOURCE_DIR"
echo "target: $MEDIA_CORE"
echo "backup: $backup_dir"

if [[ "$DRY_RUN" -eq 0 ]]; then
  mkdir -p "$backup_dir"
fi

for plugin in "${plugins[@]}"; do
  while IFS= read -r existing; do
    [[ -z "$existing" ]] && continue
    rel="${existing#"$MEDIA_CORE"/}"
    dest="$backup_dir/$rel"
    echo "[BACKUP] $existing -> $dest"
    if [[ "$DRY_RUN" -eq 0 ]]; then
      mkdir -p "$(dirname "$dest")"
      mv "$existing" "$dest"
    fi
  done < <(find_installed_bundles "$plugin")
done

for plugin in "${plugins[@]}"; do
  source_bundle="$(find_source_bundle "$plugin")"
  dest_bundle="$MEDIA_CORE/$plugin.plugin"
  echo "[INSTALL] $source_bundle -> $dest_bundle"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    ditto "$source_bundle" "$dest_bundle"
  fi
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[OK] dry run complete"
  exit 0
fi

for plugin in "${plugins[@]}"; do
  installed=()
  while IFS= read -r bundle; do
    [[ -z "$bundle" ]] && continue
    installed+=("$bundle")
  done < <(find_installed_bundles "$plugin")
  if [[ "${#installed[@]}" -ne 1 ]]; then
    echo "[FAIL] expected exactly one $plugin.plugin under MediaCore, found ${#installed[@]}" >&2
    printf '%s\n' "${installed[@]}" >&2
    exit 1
  fi
  source_bundle="$(find_source_bundle "$plugin")"
  source_binary="$source_bundle/Contents/MacOS/$plugin"
  installed_binary="${installed[0]}/Contents/MacOS/$plugin"
  if [[ ! -f "$installed_binary" ]]; then
    echo "[FAIL] installed binary missing: $installed_binary" >&2
    exit 1
  fi
  source_sha="$(shasum -a 256 "$source_binary" | awk '{print $1}')"
  installed_sha="$(shasum -a 256 "$installed_binary" | awk '{print $1}')"
  if [[ "$source_sha" != "$installed_sha" ]]; then
    echo "[FAIL] installed binary hash mismatch for $plugin" >&2
    echo "source:    $source_sha $source_binary" >&2
    echo "installed: $installed_sha $installed_binary" >&2
    exit 1
  fi
  codesign --verify "${installed[0]}"
  echo "[OK] $plugin.plugin installed sha256=$installed_sha"
done

echo "[OK] installed ${#plugins[@]} OLM plug-ins"
echo "backup: $backup_dir"
