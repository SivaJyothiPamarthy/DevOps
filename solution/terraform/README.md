# Terraform — AWS eu-north-1 (Stockholm)

```
bootstrap/          one-time S3 state bucket (versioned, encrypted, private)
modules/platform/   VPC (3 AZ) + EKS + ECR + GitHub OIDC deploy role
envs/staging/       thin root module: backend + inputs
envs/production/    same module, different inputs (HA NAT, on-demand nodes)
```

```bash
cd bootstrap && terraform init && terraform apply -var state_bucket_name=fikapay-tfstate-<acct>
cd ../envs/staging && terraform init && terraform plan -out tf.plan && terraform apply tf.plan
aws eks update-kubeconfig --region eu-north-1 --name fikapay-staging
```

Design notes (good interview talking points):
- **One module, many envs** — environments differ only by inputs, so staging really tests production's code.
- **Separate state per env** — a bad `apply` in staging can't touch production; smaller blast radius.
- **State locking** with S3 native lockfile; versioned bucket for recovery.
- **No static AWS keys in CI** — GitHub Actions assumes a role via OIDC, scoped to one GitHub Environment.
- **Immutable ECR tags** — the SHA that passed staging is byte-for-byte what reaches production.
- **Cost**: staging uses one NAT + Spot nodes; production uses NAT per AZ + on-demand.
- In CI: `terraform fmt -check`, `terraform validate`, `tflint`, `checkov`/`trivy config`, plan posted on the PR, apply on merge.
