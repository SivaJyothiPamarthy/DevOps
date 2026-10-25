# DevOps interview questions with model answers

Answer out loud, in 1–2 minutes each. Good answers: **definition → how it works → trade-off → a real example from your experience.**

- [Linux & networking](#linux--networking)
- [Containers & Docker](#containers--docker)
- [Kubernetes](#kubernetes)
- [CI/CD & GitOps](#cicd--gitops)
- [Infrastructure as Code (Terraform)](#infrastructure-as-code-terraform)
- [Cloud (AWS / GCP / Azure)](#cloud-aws--gcp--azure)
- [Observability & SRE](#observability--sre)
- [Security & compliance](#security--compliance)
- [Behavioural (Swedish-style)](#behavioural-swedish-style)

---

## Linux & networking

**1. What happens when you type `https://klarna.com` in a browser?**
DNS resolution (browser cache → OS → resolver → root → TLD → authoritative, returns A/AAAA, often via CDN CNAME) → TCP 3-way handshake → TLS handshake (ClientHello with SNI, cert validation against CA chain, key exchange) → HTTP request (HTTP/2 or HTTP/3 over QUIC) → load balancer → backend → response → rendering. Mention where caching and CDNs fit, and where things fail (DNS TTLs, expired certs).

**2. Load average is 20 on a 4-core machine. What do you check?**
Load counts runnable *and* uninterruptible (D-state, usually I/O) tasks. `top`/`htop` for CPU vs `wa`; `vmstat 1` (r vs b columns), `iostat -x 1` (disk %util, await), `ps -eo state,pid,cmd | grep ^D`. High load with idle CPU ⇒ I/O or NFS problem, not CPU.

**3. Disk is 100% full but `du` shows much less. Why?**
A process holds a deleted file open (typically a log rotated without `copytruncate`/reload). `lsof +L1` finds it; restart/reload the process or truncate via `/proc/<pid>/fd/<n>`. Also check inodes with `df -i`.

**4. Explain the difference between TCP and UDP. When use UDP?**
TCP: connection-oriented, ordered, reliable, congestion control. UDP: connectionless, no guarantees, low overhead. UDP for DNS, video/voice, game state (King!), QUIC/HTTP3 (which rebuilds reliability in user space).

**5. A service can't reach another service. Walk through debugging.**
Layer by layer: DNS (`dig`, `nslookup`), IP routing (`ip route`, `traceroute`), port reachability (`nc -vz host port`, `curl -v`), firewall/security groups/NetworkPolicy, TLS (`openssl s_client -connect host:443`), then application logs. In K8s: `kubectl get endpoints svc` — empty endpoints means the selector or readiness is wrong.

**6. What is a zombie process vs an orphan?**
Zombie: exited, but parent hasn't `wait()`ed — holds a PID table entry only. Orphan: parent died, re-parented to PID 1. In containers, if your app is PID 1 and doesn't reap children you get zombies → use `tini` / `--init` or exec form.

**7. Signals: SIGTERM vs SIGKILL?**
SIGTERM (15) can be caught for graceful shutdown; SIGKILL (9) can't. Kubernetes sends SIGTERM, waits `terminationGracePeriodSeconds`, then SIGKILL. Shell-form `CMD` makes `sh` PID 1, which doesn't forward signals ⇒ always use exec form.

**8. What's in `/etc/resolv.conf` in a Kubernetes pod and what is `ndots:5`?**
Points to CoreDNS, search domains `<ns>.svc.cluster.local svc.cluster.local cluster.local`. `ndots:5` means names with fewer than 5 dots try search domains first → external lookups like `api.stripe.com` generate several failed queries. Fix: use FQDN with trailing dot or lower ndots via `dnsConfig`.

## Containers & Docker

**9. Container vs VM?**
Containers share the host kernel and isolate with namespaces (pid, net, mnt, uts, ipc, user) + cgroups (resource limits). VMs virtualize hardware with their own kernel. Containers: faster, lighter, weaker isolation. For untrusted multi-tenant code: gVisor, Kata, Firecracker.

**10. How do you make a Docker image small and secure?**
Multi-stage builds, slim/distroless base, pin version (and digest), `.dockerignore`, combine layers, no build tools in runtime image, non-root `USER`, no secrets in layers (use BuildKit `--secret`), scan with Trivy/Grype, sign with cosign, generate SBOM. See [`solution/app/Dockerfile`](../solution/app/Dockerfile).

**11. `CMD` vs `ENTRYPOINT`? Shell vs exec form?**
ENTRYPOINT = the executable; CMD = default args (or the command if no ENTRYPOINT). Exec form (`["app"]`) runs the binary as PID 1 and receives signals; shell form wraps in `/bin/sh -c`.

**12. `COPY` vs `ADD`?**
`COPY` copies local files. `ADD` also extracts tarballs and fetches URLs — implicit behaviour, so prefer `COPY`.

**13. Why does layer order matter?**
Cache invalidation: everything after a changed layer rebuilds. Copy dependency manifests and install deps before copying source code.

**14. Your container is OOMKilled. What now?**
`kubectl describe pod` shows `OOMKilled` / exit code 137. Check actual usage (`kubectl top`, Prometheus `container_memory_working_set_bytes`), look for leaks, check runtime awareness of cgroup limits (old JVMs: use `-XX:MaxRAMPercentage`), raise the limit if usage is legitimate.

## Kubernetes

**15. Explain the Kubernetes architecture.**
Control plane: kube-apiserver (only component talking to etcd), etcd (state), scheduler (places pods), controller-manager (reconcile loops: Deployment→ReplicaSet→Pods), cloud-controller-manager. Nodes: kubelet (runs pods via CRI, e.g. containerd), kube-proxy (Service rules via iptables/IPVS, or replaced by Cilium eBPF), CNI plugin.

**16. What happens when you run `kubectl apply -f deployment.yaml`?**
kubectl → apiserver (authn, authz/RBAC, mutating admission, schema validation, validating admission e.g. OPA/Kyverno) → stored in etcd → Deployment controller creates ReplicaSet → ReplicaSet controller creates Pods → scheduler assigns node (filter + score) → kubelet pulls image, CNI sets up network, starts containers → probes pass → pod added to Service Endpoints/EndpointSlices → kube-proxy updates rules → traffic flows.

**17. Liveness vs readiness vs startup probes?**
Liveness: restart if stuck — must NOT check dependencies (a DB outage would restart every pod). Readiness: remove from Service endpoints when it can't serve. Startup: protects slow-starting apps from liveness kills.

**18. How do you achieve a zero-downtime deployment?**
RollingUpdate with `maxUnavailable: 0`, readiness probes, graceful SIGTERM handling, `preStop` sleep (so endpoints are removed before shutdown), PodDisruptionBudget, enough replicas spread across zones, backward-compatible DB migrations (expand/contract).

**19. Requests vs limits? Should you set CPU limits?**
Requests: used by the scheduler and guarantee a share. Limits: hard cap — memory over limit ⇒ OOMKill; CPU over limit ⇒ throttling (CFS). Many teams set memory request = limit and **no CPU limit** to avoid throttling latency spikes, relying on requests for fairness. QoS classes: Guaranteed, Burstable, BestEffort.

**20. Pod is in `CrashLoopBackOff`. Debug it.**
`kubectl describe pod` (events, exit code, last state), `kubectl logs --previous`, check config/secret mounts, command, probes too aggressive, OOM (137), missing dependency. `kubectl debug` with an ephemeral container if the image has no shell.

**21. Pod is `Pending`.**
`describe` events: insufficient CPU/memory (cluster autoscaler or Karpenter should add nodes), taints without tolerations, node affinity mismatch, PVC not bound (wrong StorageClass / AZ mismatch), quota exceeded.

**22. Service types?**
ClusterIP (internal), NodePort, LoadBalancer (cloud LB), ExternalName (DNS CNAME). Headless (`clusterIP: None`) for StatefulSets/direct pod DNS. Ingress / Gateway API for L7 routing.

**23. Deployment vs StatefulSet vs DaemonSet vs Job?**
Deployment: stateless, interchangeable pods. StatefulSet: stable identity (`db-0`), ordered rollout, per-pod PVC. DaemonSet: one pod per node (log agents, CNI). Job/CronJob: run to completion.

**24. How do you manage secrets in Kubernetes?**
Native Secrets are only base64 — enable etcd encryption at rest, restrict with RBAC. Better: External Secrets Operator syncing from AWS Secrets Manager / GCP Secret Manager / Azure Key Vault / Vault, or Sealed Secrets / SOPS for GitOps. Use workload identity (IRSA, GKE WI, Azure WI) instead of static cloud keys.

**25. HPA — how does it work? What about scaling on queue length?**
Control loop every 15s: desiredReplicas = ceil(current × currentMetric / target). Needs metrics-server for CPU/memory; custom/external metrics via Prometheus Adapter or **KEDA** (Kafka lag, SQS depth, cron).

**26. How do you upgrade a Kubernetes cluster safely?**
Read release notes and deprecated APIs (`pluto`, `kubent`), upgrade non-prod first, control plane before nodes, one minor at a time, PDBs in place, surge node pools or blue/green node groups, watch dashboards, have rollback plan (new node group).

**27. Helm vs Kustomize?**
Helm: templating + packaging + releases (good for distributing apps, many parameters). Kustomize: template-free overlays on plain YAML (good for your own services across environments). Many teams use both — Helm for third-party charts, Kustomize for in-house.

## CI/CD & GitOps

**28. Continuous delivery vs continuous deployment?**
Delivery: every change is releasable; production deploy is a manual decision. Deployment: every green change goes to production automatically.

**29. Describe a good pipeline.**
On PR: lint, unit tests, build, security scan (SAST, dependencies, image), IaC validation, preview env. On merge: build once, tag with git SHA, push, deploy to staging, integration/smoke tests, promote **the same artifact** to production (manual gate or automated canary analysis), automatic rollback. See [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

**30. What is GitOps?**
Git is the source of truth for desired state; an in-cluster agent (Argo CD, Flux) pulls and reconciles continuously. Benefits: audit trail, easy rollback (`git revert`), drift detection, no cluster credentials in CI.

**31. Blue/green vs canary vs rolling?**
Rolling: replace gradually, cheap, mixed versions. Blue/green: two full environments, switch traffic, instant rollback, 2x cost. Canary: small % of traffic to new version, measure metrics, then increase (Argo Rollouts, Flagger, service mesh). Feature flags decouple deploy from release.

**32. How do you handle database migrations in CD?**
Expand/contract: add new column (backward compatible) → deploy code that writes both → backfill → switch reads → remove old column later. Never a breaking migration in the same release as the code. Run migrations as a Job or pre-deploy step with a lock.

**33. What are DORA metrics?**
Deployment frequency, lead time for changes, change failure rate, time to restore service (MTTR). (Newer reports add reliability.) Used to measure delivery performance — popular with Spotify-style platform teams.

**34. Your pipeline takes 40 minutes. Speed it up.**
Measure first. Caching (deps, Docker layers with BuildKit/gha cache), parallel jobs, test splitting, only build what changed (monorepo tooling: Bazel, Nx, path filters), faster runners, move slow E2E tests to post-merge.

## Infrastructure as Code (Terraform)

**35. What is Terraform state and why remote state?**
Maps resources in code to real-world IDs, stores attributes for diffing. Remote (S3/GCS/Azure Blob/Terraform Cloud) for team sharing, with **locking** to prevent concurrent applies, versioning for recovery, encryption because state contains secrets.

**36. How do you structure Terraform for multiple environments?**
Reusable modules + thin root module per environment with separate state (directories, or Terragrunt). Workspaces are OK for identical envs but easy to apply to the wrong one. See [`solution/terraform/`](../solution/terraform/).

**37. Someone changed a resource manually in the console. What happens?**
Drift: next `plan` shows the diff and `apply` reverts it. Detect with scheduled `plan` in CI. Either codify the change or revert. Use `ignore_changes` only for fields managed elsewhere (e.g. desired_count by autoscaler).

**38. `terraform import`, `moved`, `removed` blocks?**
Import: bring existing resources under management (now declarative `import {}` blocks). `moved`: rename/refactor without destroy/recreate. `removed`: stop managing without destroying.

**39. `count` vs `for_each`?**
`for_each` keys by string, so removing an item from the middle doesn't shift indexes and recreate others. Prefer `for_each` for collections.

**40. How do you test Terraform?**
`fmt`, `validate`, `tflint`, security (`checkov`, `trivy config`), `terraform test` / Terratest, plan review on PR (Atlantis, Spacelift, TF Cloud), policy as code (OPA/Sentinel).

## Cloud (AWS / GCP / Azure)

**41. Design a highly available VPC.**
3 AZs, public subnets (LBs, NAT), private subnets (workloads), isolated DB subnets; NAT per AZ for prod; VPC endpoints for S3/ECR to cut NAT cost; security groups as least privilege. Region `eu-north-1` (Stockholm) or `europe-north1` (Finland, GCP) for data residency.

**42. How do workloads get cloud credentials without static keys?**
IAM roles: EC2 instance profiles, EKS IRSA / Pod Identity, GKE Workload Identity, Azure Workload Identity. CI uses OIDC federation (GitHub Actions → AWS role). No long-lived access keys.

**43. How do you reduce cloud cost?**
Visibility first (tags, cost allocation, Kubecost). Rightsize requests, autoscale (HPA + cluster autoscaler/Karpenter), Spot for stateless/CI, Savings Plans/committed use for baseline, storage lifecycle policies, kill idle environments, VPC endpoints vs NAT data charges, reduce cross-AZ traffic.

**44. Multi-region active-active — what's hard?**
Data: replication lag, conflicts, consistency (pick per data type), global databases (Spanner, DynamoDB Global Tables, Aurora Global). Routing (latency-based DNS, global LB), failover testing, cost, GDPR residency.

## Observability & SRE

**45. Monitoring vs observability?**
Monitoring: known questions (dashboards, alerts). Observability: ask new questions of the system from its outputs — metrics, logs, traces (+ profiles), correlated by trace/request IDs. OpenTelemetry as the standard.

**46. RED vs USE methods?**
RED for services: Rate, Errors, Duration. USE for resources: Utilization, Saturation, Errors. Google's four golden signals: latency, traffic, errors, saturation.

**47. SLI, SLO, SLA, error budget?**
SLI: measured indicator (% successful requests). SLO: internal target (99.9% over 30 days). SLA: contractual promise with penalties (looser than SLO). Error budget = 1 − SLO (43 min/month at 99.9%) — when spent, prioritize reliability over features.

**48. How do you avoid alert fatigue?**
Alert on symptoms (SLO burn rate) not causes (CPU 80%). Every page must be actionable, urgent, and have a runbook. Multi-window burn-rate alerts. Review alerts after every on-call shift; delete noisy ones. See [`solution/monitoring/alerts.yml`](../solution/monitoring/alerts.yml).

**49. Why are averages bad for latency?**
They hide the tail. Use percentiles (p50/p95/p99) from histograms; aggregate histograms, never average percentiles.

**50. Describe your incident process.**
Detect → declare (severity, incident commander, comms channel) → mitigate first (rollback, failover, scale) → communicate (status page, stakeholders) → resolve → **blameless postmortem** (timeline, root/contributing causes, action items with owners) → follow up.

## Security & compliance

**51. What is shift-left security in a pipeline?**
SAST (Semgrep, CodeQL), dependency scanning (Dependabot, Renovate, Snyk), secret scanning (gitleaks), image scanning (Trivy), IaC scanning (Checkov), SBOM + signing (Syft, cosign), admission policies (Kyverno/Gatekeeper) to only run signed images.

**52. A secret was committed to Git. What do you do?**
**Rotate it immediately** (assume compromised) → check access logs for misuse → remove from history (git filter-repo) and invalidate caches/forks → add pre-commit secret scanning → postmortem. Rewriting history alone is not enough.

**53. Explain least privilege in Kubernetes.**
RBAC Roles per namespace, no cluster-admin for apps, `automountServiceAccountToken: false`, Pod Security Standards (`restricted`), NetworkPolicies default-deny, non-root, read-only rootfs, drop capabilities, separate namespaces/clusters for tenants.

**54. GDPR basics a DevOps engineer should know?**
Personal data must have a legal basis, minimal collection, right to erasure, breach notification within 72 hours, data processing agreements with vendors, data residency/transfer rules (EU region, Schrems II). Practical: encrypt, restrict access, don't log personal data (or mask it), retention policies on logs and backups.

**55. What is DORA (the EU regulation, not the metrics)?**
Digital Operational Resilience Act — applies to EU financial entities (Klarna, banks, payment firms) since Jan 2025: ICT risk management, major incident reporting, resilience testing (incl. threat-led penetration testing), managing third-party ICT risk (cloud providers). Expect to mention it in fintech interviews.

## Behavioural (Swedish-style)

Use **STAR** (Situation, Task, Action, Result) and say "we" for team work, "I" for your part.

**56. Tell me about an incident you handled.** — Focus on calm mitigation, communication, blameless learning, what changed afterwards.

**57. Tell me about a time you disagreed with a teammate.** — Show you listened, used data, reached consensus or "disagree and commit". Swedish teams value consensus — avoid "I overruled them".

**58. How do you get developers to adopt your platform?** — Treat the platform as a product: talk to users, make the right way the easy way (golden paths), documentation, measure adoption, no forced migrations without value.

**59. What would you automate first in a new team?** — Ask, measure toil, pick the most frequent/risky manual step, deliver small wins.

**60. Why Stockholm / why us?** — Be specific: their product, their engineering blog posts, their tech choices, the culture (autonomy, work–life balance).

**61. Questions to ask them:** What does on-call look like and how often are you paged? How do teams deploy today, and how long from merge to production? What's the biggest reliability problem right now? How are platform priorities decided?
