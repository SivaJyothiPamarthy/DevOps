# DESIGN — orders-service (reference solution)

> Written the way you would present it in the follow-up interview: decisions,
> trade-offs, and honest gaps.

## Architecture

```
 GitHub ──PR──► Actions: lint ► test ► build ► smoke test ► Trivy scan
                    │ (main)
                    ▼
               ECR (eu-north-1, immutable SHA tags)
                    │
        ┌───────────┴─────────────┐
        ▼                         ▼
  EKS staging (auto)      EKS production (manual approval)
  ns orders-staging        ns orders-production
        │                         │
  Ingress-nginx ─► Service ─► Deployment (2–20 pods, 3 AZs) ─► /metrics ◄─ Prometheus ─► Alertmanager
```

## Key decisions

| Decision | Why | Trade-off / alternative |
|----------|-----|------------------------|
| Flask + gunicorn (threads, 1 worker/pod) | Small, well known; one process per pod keeps Prometheus metrics correct and lets K8s do the scaling | Multi-worker needs `prometheus_client` multiprocess mode |
| Multi-stage Dockerfile, slim base, UID 10001 | Small image, no compilers, non-root, works with `readOnlyRootFilesystem` | Distroless is smaller but harder to debug; `kubectl debug` covers that |
| Kustomize base + overlays | Plain YAML, no templating, easy diff per env | Helm if we needed to distribute the chart to other teams |
| `maxUnavailable: 0`, readiness, `preStop` sleep, PDB | Zero-downtime rollouts and node drains | Slightly slower rollouts |
| No CPU limit, memory limit set | Avoid CFS throttling tail latency; memory is incompressible | Needs good requests + namespace quotas for fairness |
| Topology spread across zones | Survive an AZ failure | `ScheduleAnyway` = best effort, not a hard guarantee |
| Terraform: one module, per-env root + separate state | Staging tests the same code as prod; small blast radius | Some duplication in the env folders (Terragrunt removes it) |
| GitHub OIDC → IAM role per environment | No long-lived AWS keys in GitHub; prod role only usable from the `production` environment | Initial OIDC provider setup per account |
| Immutable ECR tags + SHA | Exactly the artifact tested in staging reaches prod | Need lifecycle policy (included) |
| Push-based deploy from CI | Simple for a take-home, one tool | **Next step: GitOps with Argo CD** — no cluster creds in CI, drift detection |
| SLO 99.9% + multi-window burn-rate alerts | Page on user impact, not on CPU | Needs enough traffic for meaningful ratios |

## Security

- Non-root, read-only root FS, all capabilities dropped, seccomp `RuntimeDefault`, no privilege escalation.
- Namespace enforces Pod Security Standard `restricted`.
- NetworkPolicy: only ingress controller + monitoring namespaces can reach the pods.
- `automountServiceAccountToken: false`; IRSA/Pod Identity for AWS access when needed.
- Trivy fails the build on fixable HIGH/CRITICAL CVEs.
- EKS nodes in private subnets; ECR encrypted with KMS; state bucket encrypted, versioned, private.
- Secrets (once we have a DB): AWS Secrets Manager + External Secrets Operator — never in Git or the image.

## Rollback

1. **Automatic:** the deploy action waits for `kubectl rollout status`; on failure it runs `kubectl rollout undo`.
2. **Manual:** `kubectl rollout undo deploy/orders-service -n orders-production`, or re-run the production job of a previous green commit (images are immutable, so this is exact).
3. **Infra:** revert the Terraform PR and apply; `prevent_destroy` protects the state bucket.

## Follow-up questions — short answers

- **Add PostgreSQL?** RDS/Aurora Multi-AZ via Terraform in DB subnets, credentials in Secrets Manager synced with External Secrets, readiness checks DB connectivity (liveness doesn't), migrations as a pre-deploy Job using expand/contract, connection pooling (PgBouncer / RDS Proxy).
- **Canary?** Argo Rollouts or Flagger: 5% → 25% → 100% with Prometheus analysis on error rate and p99; auto-abort.
- **Black Friday 50x?** Load test first. Likely first bottleneck: the database, then cluster capacity (Karpenter + higher quotas), then NAT/LB limits. Pre-scale `minReplicas`, cache reads, queue writes.
- **Multi-region (Stockholm + Frankfurt)?** Same Terraform module per region, Route 53 latency/failover routing, database replication strategy is the hard part (Aurora Global: one writer region). GDPR fine — both in the EU.

## What I'd do with more time

- GitOps (Argo CD) + Argo Rollouts canaries.
- OpenTelemetry tracing; Loki for logs.
- `tflint`, `checkov`, `terraform test`; plan comments on PRs (Atlantis/Spacelift).
- Image signing (cosign) + Kyverno policy to only admit signed images; SBOM.
- Load tests (k6) in the pipeline against staging.
- Karpenter instead of managed node group autoscaling; VPC endpoints for ECR/S3 to cut NAT cost.
- Real persistence (the in-memory store loses data on restart and isn't shared between pods — acceptable only for the exercise).
