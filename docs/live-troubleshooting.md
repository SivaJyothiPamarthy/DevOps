# Live troubleshooting scenarios

In this round the interviewer describes a broken system (or gives you a
terminal) and watches **how you think**. Narrate: hypothesis → check → result
→ next step. Mitigate first, root-cause second.

---

## Scenario 1 — "Checkout is returning 502s after a deploy" (fintech classic)

**Setup:** 10 minutes ago a new version of `orders-service` was deployed. Error rate jumped from 0.1% to 15%.

<details><summary>Solution walkthrough</summary>

1. **Mitigate first:** the deploy is the obvious change → roll back.
   `kubectl rollout undo deploy/orders-service -n orders-production` (or revert in Git if using Argo CD).
   Confirm the error rate drops. Tell stakeholders.
2. **Then investigate** in staging or with the old pods safe:
   - `kubectl rollout history` / diff the manifests and image.
   - `kubectl get pods` — restarts? `kubectl logs --previous`.
   - 502 from the load balancer = backend closed the connection or wasn't ready.
3. **Common root causes:**
   - Readiness probe missing or always true → traffic sent to pods still starting.
   - No graceful shutdown: no `preStop` delay, so old pods die while still in LB endpoints.
   - App keep-alive timeout shorter than LB idle timeout → LB reuses closed connections → 502s.
     (Fix: app keepalive > LB idle timeout; see `gunicorn.conf.py`.)
   - New version needs a config/secret that doesn't exist in prod.
4. **Prevent:** canary releases with automatic rollback on error-rate SLO; smoke tests post-deploy.
</details>

---

## Scenario 2 — Pod stuck in `CrashLoopBackOff`

```text
$ kubectl get pods
orders-service-7c9f8d-x2k4p   0/1   CrashLoopBackOff   6   8m
```

<details><summary>Solution walkthrough</summary>

```bash
kubectl describe pod orders-service-7c9f8d-x2k4p   # Last State, Exit Code, Events
kubectl logs orders-service-7c9f8d-x2k4p --previous
```

| Exit code | Meaning | Typical fix |
|-----------|---------|-------------|
| 1 | App error | Read logs: missing env var, bad config, can't connect to DB |
| 126/127 | Command not executable / not found | Wrong `command`, missing binary, wrong arch image (arm64 vs amd64) |
| 137 | SIGKILL — usually OOMKilled | Raise memory limit or fix leak |
| 143 | SIGTERM | Liveness probe failing → kubelet restarts it; probe too strict or checks a dependency |

If there's no shell in the image: `kubectl debug -it <pod> --image=busybox --target=orders-service`.
</details>

---

## Scenario 3 — "The service is slow" (p99 went from 80ms to 2s)

<details><summary>Solution walkthrough</summary>

1. Scope: all endpoints or one? All pods or one? All AZs? Since when — correlate with deploys, traffic, config changes.
2. RED dashboard: did **rate** go up (load) or only **duration** (dependency/regression)?
3. USE on resources: CPU throttling (`container_cpu_cfs_throttled_periods_total`) — a CPU limit too low causes tail latency even at "50% CPU". Memory/GC pressure. Node noisy neighbours.
4. Dependencies: DB slow queries, connection pool exhaustion, DNS (ndots:5 adding lookups), external API.
5. Tracing (OpenTelemetry/Jaeger/Tempo) shows which span grew.
6. Mitigate: scale out, roll back, shed load / rate limit, raise pool sizes. Then fix root cause.
</details>

---

## Scenario 4 — Node `NotReady`, pods being evicted

<details><summary>Solution walkthrough</summary>

```bash
kubectl describe node <node>        # Conditions: MemoryPressure, DiskPressure, PIDPressure, Ready
kubectl get events -A --sort-by=.lastTimestamp | tail -30
```
- **DiskPressure**: images/logs filled the disk → kubelet garbage-collects images and evicts pods. Fix: bigger root volume, log rotation, clean up.
- **Kubelet down / network**: SSH/SSM in, `systemctl status kubelet`, `journalctl -u kubelet`, containerd status, CNI errors.
- **Cloud**: instance failing health checks, Spot interruption.
Mitigate: `kubectl cordon` + `kubectl drain --ignore-daemonsets --delete-emptydir-data`, let the autoscaler replace the node. PDBs make sure drains don't take down a service.
</details>

---

## Scenario 5 — `terraform apply` failed halfway in production

<details><summary>Solution walkthrough</summary>

- Don't panic and don't re-run blindly. Read the error.
- State is updated for resources that succeeded — run `terraform plan` to see what's left.
- **State lock stuck** (process killed): confirm no apply is running, then `terraform force-unlock <ID>`.
- Resource exists in cloud but not in state ("already exists"): `import` it.
- Prevent: plan → review → apply the **saved plan** in CI only, small changes, `prevent_destroy` on critical resources, separate state per env/component.
</details>

---

## Scenario 6 — "We got an AWS bill 3x higher than last month"

<details><summary>Solution walkthrough</summary>

1. Cost Explorer grouped by service, then by usage type, then by tag.
2. Usual suspects: NAT Gateway data processing (pods pulling images/S3 through NAT → add VPC endpoints), cross-AZ traffic, forgotten GPU/test instances, unattached EBS volumes and old snapshots, CloudWatch Logs ingestion (debug logging left on), load balancers per service.
3. Mitigate quickly, then add budgets + anomaly detection alerts, mandatory tags, auto-shutdown for non-prod.
</details>

---

## Scenario 7 — DNS resolution intermittently fails inside the cluster

<details><summary>Solution walkthrough</summary>

- Test from a pod: `kubectl run -it dnsutils --image=registry.k8s.io/e2e-test-images/jessie-dnsutils:1.3 -- nslookup orders-service`.
- Check CoreDNS pods, logs, CPU throttling; scale CoreDNS or add **NodeLocal DNSCache**.
- Known issue: conntrack race with UDP DNS → 5s timeouts; NodeLocal DNSCache or `single-request-reopen`.
- `ndots:5` causing query amplification for external names.
- Upstream VPC resolver limits (AWS: packets-per-second limit per ENI).
</details>

---

## Scenario 8 — "Pipeline is green but the new feature isn't in production"

<details><summary>Solution walkthrough</summary>

- Was the image actually pushed with the new SHA? Check registry.
- Mutable `latest` tag + `imagePullPolicy: IfNotPresent` → nodes run a cached old image. Fix: immutable SHA tags.
- Deploy step applied to the wrong cluster/namespace (kubeconfig context).
- GitOps: Argo CD app out-of-sync or auto-sync disabled; a failed hook.
- Feature flag off. CDN caching old frontend assets.
</details>

---

## Hands-on exercise: fix the broken manifest

Find at least 6 problems (answer below).

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 1
  selector:
    matchLabels: {app: api}
  template:
    metadata:
      labels: {app: web}
    spec:
      containers:
        - name: api
          image: mycompany/api:latest
          env:
            - name: DB_PASSWORD
              value: "SuperSecret123"
          livenessProbe:
            httpGet: {path: /db-check, port: 8080}
            initialDelaySeconds: 0
            periodSeconds: 1
          securityContext:
            privileged: true
```

<details><summary>Answer</summary>

1. **Selector doesn't match template labels** (`api` vs `web`) — rejected by the API server.
2. `replicas: 1` — no redundancy; no PDB, no topology spread.
3. `:latest` tag — not reproducible, rollbacks unreliable. Use immutable SHA/semver tags.
4. **Plaintext secret** in the manifest → use a Secret from External Secrets / Vault, never commit.
5. Liveness probe **checks the database** → DB blip restarts every pod (cascading failure). Liveness should be a cheap self-check; use readiness for dependencies.
6. `initialDelaySeconds: 0` + `periodSeconds: 1` → killed during startup; use a startupProbe.
7. No readiness probe → traffic before the app is ready.
8. No resource requests/limits → noisy neighbour, BestEffort QoS, first to be evicted.
9. `privileged: true` → full host access. Use `runAsNonRoot`, `allowPrivilegeEscalation: false`, drop ALL capabilities, read-only root FS.
</details>
