# Reference solution — orders-service

Solution to [`../task/TASK.md`](../task/TASK.md). Rationale and trade-offs are in [`DESIGN.md`](DESIGN.md).

```
app/            Flask service, tests, Dockerfile, gunicorn config
docker-compose.yml   app + Prometheus + Grafana for local dev
k8s/            Kustomize base + staging/production overlays
terraform/      AWS eu-north-1: VPC, EKS, ECR, OIDC deploy role, remote state
monitoring/     Prometheus scrape config, SLO burn-rate alerts, Grafana dashboard
../.github/     CI/CD pipeline + reusable deploy action
```

## Run locally

```bash
docker compose up --build
curl localhost:8080/healthz
curl -X POST localhost:8080/api/v1/orders -H 'content-type: application/json' \
     -d '{"item":"kanelbulle","amount_sek":35}'
curl localhost:8080/api/v1/orders
open http://localhost:9090   # Prometheus (alerts tab shows SLO rules)
open http://localhost:3000   # Grafana → orders → "orders-service (RED)"
```

## Tests and checks

```bash
cd app && pip install -r requirements.txt -r requirements-dev.txt
ruff check . && ruff format --check . && pytest -q

kubectl kustomize k8s/overlays/production      # render manifests
terraform -chdir=terraform fmt -check -recursive
```

## Deploy to your own AWS account

1. `terraform/bootstrap` → state bucket. Update the bucket name in `terraform/envs/*/main.tf`.
2. Create the GitHub OIDC provider in IAM once (`token.actions.githubusercontent.com`).
3. `terraform/envs/staging` and `envs/production` → `terraform apply`.
4. Install ingress-nginx and cert-manager in the clusters (or use the AWS Load Balancer Controller).
5. In GitHub: create environments `staging` and `production` (add required reviewers to production),
   and set the repository variable `AWS_ACCOUNT_ID`. Replace `123456789012` in `k8s/overlays/*`.
6. Push to `main` → the pipeline builds, pushes, deploys to staging, then waits for approval for production.

Until `AWS_ACCOUNT_ID` is set, the pipeline still runs all CI jobs and simply skips the deploy jobs.
