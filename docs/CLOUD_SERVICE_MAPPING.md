# Cloud Service Mapping

A reference for mapping the Azure services used in this project to their closest AWS and GCP
equivalents. "Closest" does not mean identical - the differences noted matter in practice.

| Concept | Azure | AWS | GCP | Notable differences |
|---|---|---|---|---|
| Managed Kubernetes | AKS | EKS | GKE | AKS's control plane is free; EKS charges per cluster-hour. GKE has an "Autopilot" mode with a different operational model than either. |
| Container registry | ACR | ECR | Artifact Registry | ACR bundles registry + geo-replication + content trust in one resource; ECR is closer to a pure registry with IAM-based access. |
| Log/metrics store | Log Analytics (under Azure Monitor) | CloudWatch Logs/Metrics | Cloud Logging / Cloud Monitoring | Log Analytics uses KQL for queries; CloudWatch Logs Insights uses its own query language; Cloud Logging uses a Lucene-like filter syntax. All three are proprietary to their cloud - none are portable. |
| APM / tracing | Application Insights | X-Ray / CloudWatch Application Signals | Cloud Trace / Cloud Profiler | Application Insights auto-instruments a wide range of .NET/Java/Node/Python frameworks with a single SDK; the AWS and GCP equivalents are more often assembled from separate services. |
| Secrets store | Key Vault | Secrets Manager (+ KMS for keys) | Secret Manager (+ Cloud KMS for keys) | Key Vault stores secrets *and* keys *and* certificates in one resource; AWS and GCP split secrets and key-management into separate services. |
| Non-human identity | Managed identity (system- or user-assigned) | IAM role (+ IRSA for EKS pods) | Service account (+ Workload Identity for GKE pods) | Conceptually the closest three-way match in this table: all three let a workload authenticate to other cloud services without a stored credential. Azure's system- vs. user-assigned distinction has no exact AWS equivalent. |
| Access control | Azure RBAC (role assignment: principal + role + scope) | IAM policies (attached to users/roles/resources) | IAM (bindings: member + role, on a resource) | Conceptually similar (principal, role, scope everywhere); the policy *language* and default-deny/allow behavior differ in the details. |
| Logical grouping | Resource Group | (no direct equivalent - closest is tagging + AWS Organizations/OUs) | Project | A GCP Project is the closest analogue (it's also a security/billing boundary, which a Resource Group is not); AWS has no single resource that plays the same role. |
| CI/CD pipeline definition | Azure DevOps Pipelines (YAML) | GitHub Actions / CodePipeline | Cloud Build / GitHub Actions | This project also includes a GitHub Actions workflow for repo-level CI, alongside the Azure DevOps pipeline for the Azure-specific flow. |

## Why this project uses Azure DevOps *and* GitHub Actions

They serve different purposes here, not the same one twice: GitHub Actions runs lightweight,
credential-free validation on every push/PR (lint, test, build, Terraform format/validate).
`pipelines/azure-pipelines.yml` is the Azure-specific illustration of what a real deployment
pipeline into ACR/AKS would look like, including the approval gate - it is not required to
validate the repository and is not wired to run automatically.
