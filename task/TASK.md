# Take-home Assignment: "Ship the Orders Service"

> Format modelled on take-homes used by Stockholm fintech / streaming / gaming
> companies. Expected effort: **3–4 hours**. Quality over quantity — it's fine
> to leave items as documented "next steps".

## Background

You've joined the Platform team at **Fika Pay**, a fast-growing Stockholm
fintech. A product team has written a small HTTP service, `orders-service`,
and needs it production-ready on Kubernetes in the cloud (`eu-north-1`,
Stockholm region — data must stay in the EU for GDPR).

The service has three endpoints today:

| Method | Path | Behaviour |
|--------|------|-----------|
| `GET`  | `/api/v1/orders` | List orders |
| `POST` | `/api/v1/orders` | Create an order `{"item": str, "amount_sek": number}` |
| `GET`  | `/api/v1/orders/<id>` | Get one order |

## Your tasks

### 1. Make the service operable (required)
- Add `GET /healthz` (liveness) and `GET /readyz` (readiness) endpoints.
- Expose Prometheus metrics on `GET /metrics` (request count + latency histogram at minimum).
- Log in structured JSON to stdout.
- Configuration via environment variables only (12-factor).
- Write unit tests.

### 2. Containerise (required)
- Write a production-grade `Dockerfile`: small image, non-root user,
  pinned base image, no secrets baked in, proper signal handling.
- Provide a `docker-compose.yml` for local development.

### 3. CI/CD (required)
Using GitHub Actions (or GitLab CI), build a pipeline that:
- Lints and tests on every pull request.
- Builds the image and scans it for vulnerabilities.
- Pushes to a registry tagged with the git SHA on `main`.
- Deploys to a `staging` environment automatically and to `production` behind a manual approval.

### 4. Kubernetes (required)
- Deployment, Service, ConfigMap, HorizontalPodAutoscaler, PodDisruptionBudget.
- Liveness/readiness probes, resource requests/limits, security context.
- Environment overlays for `staging` and `production` (Kustomize or Helm).
- Zero-downtime rolling updates.

### 5. Infrastructure as Code (required)
With Terraform, provision in AWS `eu-north-1` (or GCP `europe-north1`):
- A VPC with public and private subnets across 3 AZs.
- A managed Kubernetes cluster (EKS / GKE) with nodes in private subnets.
- A container registry.
- Remote state with locking.

### 6. Observability (bonus)
- Prometheus scrape config + a Grafana dashboard or alert rules.
- Define one **SLO** for the service and an alert based on error-budget burn rate.

### 7. Write-up (required)
A short `DESIGN.md` covering: decisions & trade-offs, security, what you'd do
with more time, and how you would roll back a bad release.

## What we evaluate

| Area | We look for |
|------|-------------|
| Correctness | It runs. `docker compose up` works; tests pass. |
| Security | Non-root, least privilege, no secrets in git, image scanning |
| Reliability | Probes, PDB, HPA, graceful shutdown, rollbacks |
| Automation | Reproducible pipeline, IaC, no click-ops |
| Communication | Clear README/DESIGN, honest trade-offs |
| Pragmatism | Right-sized — not over-engineered for a 4h task |

## Follow-up interview (expect these)

- Walk us through your pipeline. What happens when a test fails? When the deploy fails halfway?
- How would you do a canary or blue/green release here?
- The service now needs a PostgreSQL database. What changes?
- How do you handle secrets? (Vault / AWS Secrets Manager / External Secrets / SOPS)
- Traffic grows 50x during Black Friday. What breaks first?
- How would you make this multi-region (Stockholm + Frankfurt)?
- What does "production-ready" mean to you?

👉 Reference solution: [`../solution/`](../solution/) and its [`DESIGN.md`](../solution/DESIGN.md).
