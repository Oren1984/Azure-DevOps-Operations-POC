# Proposed Azure Architecture

Everything in this document describes what `infra/terraform` *would* create if applied against a
real subscription. **Nothing here has been deployed.** See
[SECURITY_AND_COST.md](SECURITY_AND_COST.md) for cost and safety details, and
[../infra/terraform](../infra/terraform) for the actual (unapplied) configuration.

## Diagram

```mermaid
flowchart TB
    subgraph RG["Resource Group: rg-adops-poc-dev"]
        ACR["Azure Container Registry\n(acr-adops-poc-dev)"]
        AKS["AKS Cluster\n(aks-adops-poc-dev)\nsystem-assigned identity"]
        KV["Key Vault\n(kv-adops-poc-dev)\nRBAC-authorized"]
        LAW["Log Analytics Workspace\n(law-adops-poc-dev)"]
        AI["Application Insights\n(workspace-based)"]
        UAI["User-assigned managed identity\n(workload)"]
    end

    Dev[Developer / Pipeline] -->|docker build & push| ACR
    ACR -->|AcrPull via RBAC| AKS
    AKS -->|Container Insights / oms_agent| LAW
    AKS -->|diagnostic settings\n(control-plane logs, metrics)| LAW
    LAW --- AI
    UAI -->|Key Vault Secrets User| KV
    AKS -.->|would host a pod using UAI\nvia workload identity federation, not yet wired| UAI
```

## Services and why each appears

- **Resource Group** - a container for every resource in this POC, so the whole thing can be
  identified (and, in a real subscription, torn down) as one unit.
- **Azure Container Registry (ACR)** - stores the application's Docker image after a pipeline
  builds it. AKS pulls from here instead of a public registry.
- **Azure Kubernetes Service (AKS)** - runs the application container. Uses a system-assigned
  managed identity, granted `AcrPull` on the registry via Azure RBAC, so no registry credential
  is ever stored in a Kubernetes Secret.
- **Log Analytics Workspace** - the destination for both AKS Container Insights (via the
  `oms_agent` add-on) and an `azurerm_monitor_diagnostic_setting` capturing AKS control-plane
  logs (`kube-apiserver`, `kube-controller-manager`) and platform metrics. This is the single
  place logs and metrics from this POC would land.
- **Application Insights** (workspace-based) - application-level telemetry (requests,
  dependencies, exceptions), stored in the same Log Analytics workspace rather than a separate
  classic resource.
- **Key Vault** - where a real deployment would store the one secret this app can use (an Azure
  OpenAI API key, only if the optional AI path were ever enabled). RBAC-authorized, not the
  legacy access-policy model.
- **Managed identity** - two are modeled: AKS's own system-assigned identity (for `AcrPull`),
  and a separate user-assigned identity representing the application workload (granted `Key
  Vault Secrets User`). Neither has a stored password or client secret.
- **Azure RBAC** - both identity grants above (`AcrPull`, `Key Vault Secrets User`) are Azure
  RBAC role assignments scoped to a single resource, not subscription-wide access.

## What is *not* wired up, and why

A full production pattern would also configure **AKS workload identity federation**: enabling
`oidc_issuer_enabled`/`workload_identity_enabled` on the cluster, creating an
`azurerm_federated_identity_credential` linking the user-assigned identity to a Kubernetes
ServiceAccount, and annotating that ServiceAccount so a pod can obtain a token for the identity
without any credential ever existing inside the cluster. That federation step is intentionally
left out here to keep the Terraform surface small for a POC - the identity and its RBAC grant are
modeled so the concept is visible, but the last wiring step is documented rather than built.
Networking is similarly minimal: the AKS module uses `kubenet` rather than Azure CNI or a custom
VNet/subnet layout, which is enough to demonstrate the cluster but is not what a network-team
would sign off on for a production workload.

## Deployment flow (if this were ever run for real)

1. A commit to `main` triggers CI (GitHub Actions or Azure DevOps) - lint, test, Docker build,
   Terraform format/validate.
2. A human enables the Azure DevOps pipeline's `deployToAzure` parameter and it builds and pushes
   the image to ACR (`pipelines/azure-pipelines.yml`, "PushImage" stage).
3. Deployment to AKS is gated behind an Azure DevOps **Environment approval** - a named person or
   group must approve before `KubernetesManifest@1` applies `infra/kubernetes/*.yaml`.
4. AKS pulls the new image from ACR (via the cluster's `AcrPull` role assignment), performs a
   rolling update (see `infra/kubernetes/deployment.yaml`), and the readiness probe on `/ready`
   gates traffic to new pods.
5. Logs and metrics flow to Log Analytics / Application Insights throughout, independent of
   whether the rollout succeeds.

## Security boundaries

- No application credential is stored in Kubernetes or in source control; access to ACR and Key
  Vault is via managed identity + RBAC.
- Key Vault is RBAC-authorized (`enable_rbac_authorization = true`), not the legacy access-policy
  model, so grants are ordinary, auditable role assignments.
- The AKS cluster's own identity is scoped to exactly one permission it needs (`AcrPull` on one
  registry) rather than a broad Contributor-style role.
- `tenant_id` and subscription context are never hardcoded in this repository - they come from
  `az login` or a pipeline's service connection at apply time (see
  `infra/terraform/environments/dev/providers.tf`).
