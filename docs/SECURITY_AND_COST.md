# Security and Cost

## Confirmation

- **No Azure resource has been provisioned by this project.** `terraform apply` has not been run.
- **No cloud cost has been incurred.** Everything runnable in this repository (the app, its
  tests, Docker Compose) runs entirely locally.

## Secrets handling

- No secret is committed to source control. `.env.example` documents every configuration
  variable with safe placeholder values; a real `.env` is gitignored.
- The only credential the application can use is an optional Azure OpenAI API key
  (`APP_AZURE_OPENAI_API_KEY`), and the app works correctly with it unset (falls back to the
  deterministic assistant - see `app/integrations/ai_assistant.py`).
- `infra/kubernetes/secret.example.yaml` is explicitly an example, not applied by default, and
  documents why a real deployment would prefer reading the secret from Key Vault via managed
  identity over hand-managing a Kubernetes Secret at all.

## Least privilege

- The AKS cluster's managed identity is granted exactly one role (`AcrPull`) on exactly one
  resource (the ACR instance), not a subscription- or resource-group-wide role.
- The workload's user-assigned identity is granted exactly one role (`Key Vault Secrets User`)
  on exactly one resource (the Key Vault instance).
- Key Vault uses `enable_rbac_authorization = true`, so access is through ordinary, auditable
  role assignments rather than the legacy access-policy model.

## Managed identity

Both identities modeled in `infra/terraform/environments/dev/main.tf` (the AKS system-assigned
identity, and the standalone user-assigned workload identity) mean no application code or
Kubernetes manifest in this repository ever needs to hold a client secret or connection string
for Azure itself. See [AZURE_ARCHITECTURE.md](AZURE_ARCHITECTURE.md) for what is and is not fully
wired (workload identity *federation* - the last step that would let a pod actually assume the
workload identity - is documented but not built, to keep the Terraform surface small).

## Azure RBAC

Every role assignment in this project is scoped to a single resource:

```hcl
resource "azurerm_role_assignment" "acr_pull" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.this.kubelet_identity[0].object_id
}
```

There is no `Contributor`, `Owner`, or subscription-scoped assignment anywhere in the
configuration.

## Container security

- The Docker image runs as a non-root user (`appuser`, uid 1000) - see `Dockerfile`.
- The base image is `python:3.12-slim`, chosen to minimize the package surface compared to a
  full `python:3.12` image. A vulnerability scan of any base image will still surface findings
  from upstream OS packages; this is normal and would be addressed in a real deployment by
  scanning in CI (e.g. Trivy) and rebuilding on a cadence, which is out of scope for this POC.
- `ACR admin_enabled = false` - registry access is via managed identity + RBAC, not the
  registry's built-in admin account.
- No privileged container, hostPath mount, or `hostNetwork` is used anywhere in
  `infra/kubernetes/`.

## Cloud cost risks (if this were ever applied)

Applying `infra/terraform` against a real subscription would create billable resources. Approximate,
non-binding cost drivers to be aware of:

| Resource | Cost driver |
|---|---|
| AKS | Worker node VM(s) (`Standard_B2s` x `node_count`, default 1) - the AKS control plane itself is free for the Free tier used here |
| Log Analytics Workspace | Data ingestion volume + retention (`retention_in_days`, default 30) |
| Application Insights | Data ingestion volume (shares the Log Analytics workspace) |
| ACR | Storage (Basic SKU is the lowest cost tier) |
| Key Vault | Per-operation cost, typically negligible at POC scale |

None of these are provisioned by this repository as delivered. If you choose to run
`terraform apply` yourself against your own subscription, do so deliberately, with a plan to
`terraform destroy` afterward, and review the plan output first.
