# Azure Glossary

Plain explanations of the Azure terms this project uses, for quick reference.

**Azure DevOps** - Microsoft's suite of developer tools (Boards, Repos, Pipelines, Artifacts,
Test Plans). This project only uses **Pipelines**: `pipelines/azure-pipelines.yml` defines a
build/validate/deploy pipeline as YAML, similar in spirit to a GitHub Actions workflow or a
GitLab CI file.

**ACR (Azure Container Registry)** - a private Docker registry hosted in Azure. A pipeline
builds an image and pushes it here; AKS then pulls from it. Comparable to Docker Hub (private
repos), AWS ECR, or Google Artifact Registry.

**AKS (Azure Kubernetes Service)** - managed Kubernetes: Azure runs and patches the control
plane, you manage node pools and workloads. Comparable to Amazon EKS or Google GKE.

**Azure Monitor** - the umbrella platform for collecting metrics, logs, and alerts across Azure
resources. Log Analytics and Application Insights are both part of it; "Azure Monitor" is often
used loosely to mean "the whole observability stack," and diagnostic settings (like the one in
`infra/terraform/modules/monitoring`) are how a resource's data gets *into* Azure Monitor.

**Log Analytics** - a query-able log store (using the Kusto Query Language, KQL) that sits
underneath Azure Monitor. AKS Container Insights, diagnostic settings, and Application Insights
can all write into one Log Analytics **workspace**.

**Application Insights** - application performance monitoring (APM): request rates, response
times, dependency calls, exceptions. In its modern form it is "workspace-based," meaning its data
actually lives in a Log Analytics workspace rather than a separate store.

**Key Vault** - a managed store for secrets, keys, and certificates. Applications read from it at
runtime instead of having a secret baked into an image, a config file, or a Kubernetes Secret.

**Managed identity** - an identity Azure automatically manages for a resource (like an AKS
cluster or a VM), so that resource can authenticate to other Azure services without a stored
password or client secret. **System-assigned** is tied to the resource's lifecycle (deleted with
it); **user-assigned** is a standalone resource that can be attached to more than one thing.

**Entra ID** (formerly Azure Active Directory / Azure AD) - Azure's identity provider: the
directory of users, groups, service principals, and managed identities that Azure RBAC grants
are made against.

**Azure RBAC** - role-based access control for Azure resources: a **role assignment** grants a
**principal** (a user, group, service principal, or managed identity) a **role** (a set of
permissions, e.g. `AcrPull`) at a **scope** (a resource, resource group, or subscription). This
project's Terraform grants two narrow, resource-scoped roles rather than anything
subscription-wide.

**Resource Group** - a logical container for related Azure resources, mainly for lifecycle and
access-management purposes (delete the group, delete everything in it). It has no runtime
behavior of its own.

**Service connection** - an Azure DevOps concept: a stored, scoped credential (usually backed by
a Entra ID service principal or workload identity) that lets a pipeline authenticate to an
external service (an Azure subscription, an ACR, a Kubernetes cluster) without embedding a
secret in the pipeline YAML itself. `pipelines/azure-pipelines.yml` references two
(`acr-service-connection`, `aks-service-connection`) that would need to be created manually in
Azure DevOps project settings before the deploy stages could ever run for real.
