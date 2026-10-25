# DevOps / Platform system design rounds

Framework (works for every question, ~45 min):

1. **Clarify** (5 min) — users, scale, SLOs, constraints (budget, compliance, team size, existing stack).
2. **High-level design** (10 min) — draw the boxes.
3. **Deep dive** (20 min) — the interviewer picks: deployments, data, security, observability, failure modes.
4. **Trade-offs & evolution** (10 min) — what you'd do at 10x, what you'd cut for an MVP.

---

## 1. "Design a CI/CD platform for 200 engineering teams" (Spotify / H&M style)

<details><summary>Answer outline</summary>

**Clarify:** monorepo or polyrepo? Languages? Cloud? Deploys/day? Compliance?

**Design:**
- **Golden path templates** (Backstage scaffolder) create repo + pipeline + K8s manifests + dashboards + alerts in one click.
- **Shared, versioned pipeline definitions** (reusable GitHub Actions workflows / GitLab CI includes) so teams don't copy-paste; platform team ships improvements to everyone.
- **Build:** ephemeral autoscaling runners (actions-runner-controller on K8s), remote build cache, artifact registry per region.
- **Supply chain:** SBOM, signing (cosign), provenance (SLSA), admission policy only runs signed images.
- **Deploy:** GitOps (Argo CD) per cluster; progressive delivery (Argo Rollouts) with automated analysis against Prometheus SLOs.
- **Guardrails, not gates:** policies as code (Kyverno/OPA), required checks, but teams own their deploy button.
- **Measure:** DORA metrics per team on a dashboard; developer surveys.

**Trade-offs:** central control vs team autonomy; shared runners cost vs isolation (security of untrusted PRs); one big Argo CD vs per-cluster instances.
</details>

---

## 2. "Design the infrastructure for a payments API with 99.99% availability" (Klarna style)

<details><summary>Answer outline</summary>

- 99.99% = ~4.3 min downtime/month → no single AZ, no manual failover, deploys must be safe.
- **Multi-AZ** active everywhere; consider **multi-region** (Stockholm + Frankfurt/Ireland) active-passive with tested failover, or active-active for read paths.
- **Data:** managed PostgreSQL with synchronous standby across AZs (RDS Multi-AZ / Aurora), PITR backups, cross-region replica. Idempotency keys on payment requests so retries never double-charge. Outbox pattern + Kafka for events.
- **Traffic:** global LB / Route 53 health-checked failover, WAF, rate limiting, mTLS between services (service mesh).
- **Deploys:** canary + automatic rollback, feature flags, expand/contract migrations, change freeze windows only if needed.
- **Security/compliance:** PCI scope minimisation (tokenise card data, isolate CDE in separate accounts/clusters), KMS encryption, audit logs to immutable storage, JIT access, DORA incident reporting.
- **Observability:** SLOs per critical user journey (authorise payment), burn-rate alerts, tracing, synthetic checks from outside.
- **Resilience testing:** game days, chaos engineering (kill AZ in staging), DR drills with measured RTO/RPO.
</details>

---

## 3. "Design centralized logging for 500 microservices" (any company)

<details><summary>Answer outline</summary>

- **Collection:** DaemonSet agent (Fluent Bit / Vector / OTel Collector) reading container stdout; apps log structured JSON with trace IDs.
- **Transport:** buffer through Kafka for back-pressure and fan-out.
- **Storage:** hot (7–14 days, searchable: Loki / OpenSearch / Elastic) + cold (S3/GCS, Parquet, queried with Athena/BigQuery) for compliance retention.
- **Cost control:** drop debug logs in prod, sample high-volume logs, label cardinality limits (Loki), per-team quotas and chargeback.
- **Security/GDPR:** mask PII at the agent, RBAC per team, retention policies, encryption.
- **Trade-off:** Loki (cheap, index labels only) vs Elasticsearch (full-text, expensive at scale).
</details>

---

## 4. "A game launches tomorrow, 10x normal traffic expected" (King style)

<details><summary>Answer outline</summary>

- Load test now at 10–15x with realistic traffic (k6, Locust, Gatling); find the first bottleneck.
- Pre-scale: raise HPA minReplicas, pre-warm nodes / LBs, raise cloud quotas (often forgotten!).
- Caches and CDNs for static/semi-static content; protect DB with connection pooling, read replicas, queues.
- Graceful degradation: feature flags to turn off non-essential features (leaderboards, recommendations), rate limiting, queue-based admission.
- War room: dashboards, on-call roster, rollback plan, comms plan. Freeze unrelated changes.
- After: cost review, scale down, postmortem even if it went well.
</details>

---

## 5. "Migrate 50 VMs-based services to Kubernetes" (banks / Ericsson / consultancies)

<details><summary>Answer outline</summary>

- Inventory and classify (stateless vs stateful, dependencies, owners, criticality). Start with low-risk stateless services.
- Build the platform first: cluster(s) via Terraform, ingress, cert-manager, external-dns, secrets, observability, CI/CD templates.
- Containerise with 12-factor fixes (config from env, logs to stdout, graceful shutdown).
- Migrate traffic gradually (weighted DNS / LB), keep VMs as rollback, decommission when stable.
- Keep stateful DBs on managed services rather than in the cluster at first.
- Train teams; pair with them; document. Measure: deploy frequency before vs after.
</details>
