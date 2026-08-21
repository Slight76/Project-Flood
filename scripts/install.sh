#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--force] [--mode full|adapter] <target-repository>"
}

force=false
mode="full"
target_root=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)
      force=true
      shift
      ;;
    --mode)
      [[ $# -ge 2 ]] || { usage >&2; exit 2; }
      mode="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -* )
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      [[ -z "${target_root}" ]] || { usage >&2; exit 2; }
      target_root="$1"
      shift
      ;;
  esac
done

if [[ -z "${target_root}" || ( "${mode}" != "full" && "${mode}" != "adapter" ) ]]; then
  usage >&2
  exit 2
fi

to_bash_path() {
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "$1"
  else
    printf '%s\n' "$1"
  fi
}

script_path="$(to_bash_path "${BASH_SOURCE[0]}")"
target_root="$(to_bash_path "${target_root}")"

if [[ ! -d "${target_root}" ]]; then
  echo "Target directory does not exist: ${target_root}" >&2
  exit 1
fi

script_dir="$(cd "$(dirname "${script_path}")" && pwd)"
source_root="$(cd "${script_dir}/../template" && pwd)"
target_root="$(cd "${target_root}" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  python_command=(python3)
elif command -v python >/dev/null 2>&1; then
  python_command=(python)
else
  echo "Python 3 is required." >&2
  exit 1
fi

if ! "${python_command[@]}" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"; then
  echo "Project Flood requires Python 3.10 or newer." >&2
  exit 1
fi

if ! "${python_command[@]}" -c "import yaml" >/dev/null 2>&1; then
  echo "PyYAML is required. Run: ${python_command[*]} -m pip install -r ${script_dir}/../requirements.txt" >&2
  exit 1
fi

arguments=(
  "${script_dir}/flood.py"
  install
  --source "${source_root}"
  --target "${target_root}"
  --mode "${mode}"
)
if [[ "${force}" == true ]]; then
  arguments+=(--force)
fi

"${python_command[@]}" "${arguments[@]}"
echo "Next: open the repository in VS Code, select Flood Squad Lead, and invoke flood-repository-onboarding."
