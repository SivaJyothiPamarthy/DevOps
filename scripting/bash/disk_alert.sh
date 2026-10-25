#!/usr/bin/env bash
# Print filesystems above a usage threshold. Exit 1 if any found, 0 otherwise.
# Usage: disk_alert.sh [THRESHOLD_PERCENT]   (default 80)
# Input can be faked for testing with DF_CMD="cat fixture.txt".
set -euo pipefail

threshold="${1:-80}"
if ! [[ "$threshold" =~ ^[0-9]+$ ]] || (( threshold > 100 )); then
  echo "usage: $0 [threshold 0-100]" >&2
  exit 2
fi

df_cmd="${DF_CMD:-df -P -x tmpfs -x devtmpfs -x overlay -x squashfs}"
found=0

# -P = POSIX output: one line per filesystem, columns never wrap
while read -r fs _size _used _avail pct mount; do
  usage="${pct%\%}"
  [[ "$usage" =~ ^[0-9]+$ ]] || continue
  if (( usage >= threshold )); then
    printf 'ALERT %s mounted on %s is at %s%% (threshold %s%%)\n' "$fs" "$mount" "$usage" "$threshold"
    found=1
  fi
done < <($df_cmd | tail -n +2)

exit "$found"
