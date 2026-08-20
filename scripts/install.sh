#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 [--force] <target-repository>"
}

force=false
if [[ "${1:-}" == "--force" ]]; then
  force=true
  shift
fi

if [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_root="$(cd "${script_dir}/../template" && pwd)"
target_root="$1"

if [[ ! -d "${target_root}" ]]; then
  echo "Target directory does not exist: ${target_root}" >&2
  exit 1
fi

target_root="$(cd "${target_root}" && pwd)"
conflicts=()
shopt -s globstar dotglob nullglob
source_files=("${source_root}"/**)

for source_file in "${source_files[@]}"; do
  [[ -f "${source_file}" ]] || continue
  relative_path="${source_file#"${source_root}/"}"
  destination="${target_root}/${relative_path}"
  if [[ -e "${destination}" ]]; then
    conflicts+=("${relative_path}")
  fi
done

if [[ ${#conflicts[@]} -gt 0 && "${force}" != true ]]; then
  echo "No files were copied because these destinations already exist:" >&2
  printf '  %s\n' "${conflicts[@]}" >&2
  echo "Merge them manually, or rerun with --force to back them up and replace them." >&2
  exit 1
fi

backup_root=""
if [[ ${#conflicts[@]} -gt 0 ]]; then
  backup_root="${target_root}/.project-flood-backup/$(date -u +%Y%m%d-%H%M%S)"
  for relative_path in "${conflicts[@]}"; do
    mkdir -p "${backup_root}/$(dirname "${relative_path}")"
    cp -p "${target_root}/${relative_path}" "${backup_root}/${relative_path}"
  done
fi

for source_file in "${source_files[@]}"; do
  [[ -f "${source_file}" ]] || continue
  relative_path="${source_file#"${source_root}/"}"
  destination="${target_root}/${relative_path}"
  mkdir -p "$(dirname "${destination}")"
  cp -p "${source_file}" "${destination}"
done

mkdir -p "${target_root}/.agent-team/scratch"

echo "Project Flood installed into ${target_root}"
if [[ -n "${backup_root}" ]]; then
  echo "Replaced files were backed up to ${backup_root}"
fi
echo "Next: open the repository in VS Code, select Squad Lead, and run /onboard-repository."
