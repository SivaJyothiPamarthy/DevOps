#!/usr/bin/env bash
# Poll URL until HTTP 200, with exponential backoff (1,2,4,8... capped at MAX_DELAY).
# Usage: wait_for_healthy.sh URL [MAX_ATTEMPTS=8] [MAX_DELAY=30]
set -euo pipefail

url="${1:?usage: $0 URL [MAX_ATTEMPTS] [MAX_DELAY]}"
max_attempts="${2:-8}"
max_delay="${3:-30}"
delay=1

for (( attempt = 1; attempt <= max_attempts; attempt++ )); do
  code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$url" || true)"
  if [[ "$code" == "200" ]]; then
    echo "healthy after $attempt attempt(s)"
    exit 0
  fi
  echo "attempt $attempt/$max_attempts: got '${code:-none}', retrying in ${delay}s" >&2
  if (( attempt < max_attempts )); then
    sleep "$delay"
    delay=$(( delay * 2 > max_delay ? max_delay : delay * 2 ))
  fi
done

echo "unhealthy after $max_attempts attempts" >&2
exit 1
