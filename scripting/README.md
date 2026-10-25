# Scripting tasks (screening round)

Typical 30–45 min live-coding exercises. Try each before opening the solution.

| # | Task | Solution |
|---|------|----------|
| 1 | **Log analyzer** — Given an nginx access log, print: total requests, top 5 client IPs, 5xx error rate, p95 response time, and the slowest endpoint. Handle malformed lines. | [`log-analyzer/analyze.py`](log-analyzer/analyze.py) |
| 2 | **Disk alert** — Bash script that prints every mounted filesystem above a usage threshold (default 80%) and exits non-zero if any are found (so it can run from cron/monitoring). | [`bash/disk_alert.sh`](bash/disk_alert.sh) |
| 3 | **Wait for healthy** — Bash script that polls a URL until it returns HTTP 200, with exponential backoff and a max number of attempts. Used in deploy pipelines. | [`bash/wait_for_healthy.sh`](bash/wait_for_healthy.sh) |
| 4 | **One-liners** — classic shell questions | below |

Run the tests: `pip install pytest && pytest -q scripting`

## 4. One-liners interviewers love

```bash
# Top 10 IPs in an access log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head

# Count HTTP status codes
awk '{print $9}' access.log | sort | uniq -c | sort -rn

# Which process is listening on port 8080?
ss -ltnp 'sport = :8080'          # or: lsof -i :8080

# Largest 10 directories under /var
du -xh /var 2>/dev/null | sort -rh | head

# Disk "full" but du shows little? Find deleted-but-open files
lsof +L1

# Find files modified in the last 24h larger than 100MB
find / -xdev -type f -mtime -1 -size +100M 2>/dev/null

# Replace a string in all YAML files in place
grep -rl 'old-registry' --include='*.yaml' . | xargs sed -i 's/old-registry/new-registry/g'

# Follow logs of all pods of a deployment
kubectl logs -f deploy/orders-service --all-containers --max-log-requests=10

# Pods not Running, across all namespaces
kubectl get pods -A --field-selector=status.phase!=Running

# Decode a Kubernetes secret
kubectl get secret db -o jsonpath='{.data.password}' | base64 -d
```
