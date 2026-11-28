#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
skills_source="$repository_root/skills"
if [[ $# -gt 1 ]]; then
  printf 'Usage: %s [skills-home]\n' "$0" >&2
  exit 2
fi
skills_home="${1:-$HOME/.agents/skills}"
link_path="$skills_home/ai-skills"

if [[ ! -d "$skills_source" ]]; then
  printf 'Skills folder not found: %s\n' "$skills_source" >&2
  exit 1
fi

mkdir -p "$skills_home"

if [[ -L "$link_path" ]]; then
  link_target="$(cd "$link_path" 2>/dev/null && pwd -P)" || {
    printf 'Existing link is broken; refusing to replace it: %s\n' "$link_path" >&2
    exit 1
  }
  if [[ "$link_target" == "$skills_source" ]]; then
    printf 'Already linked: %s -> %s\n' "$link_path" "$skills_source"
    exit 0
  fi
  printf 'Existing link points elsewhere; refusing to replace it: %s -> %s\n' "$link_path" "$link_target" >&2
  exit 1
fi

if [[ -e "$link_path" ]]; then
  printf 'Path already exists; refusing to replace it: %s\n' "$link_path" >&2
  exit 1
fi

ln -s "$skills_source" "$link_path"
printf 'Linked: %s -> %s\n' "$link_path" "$skills_source"
