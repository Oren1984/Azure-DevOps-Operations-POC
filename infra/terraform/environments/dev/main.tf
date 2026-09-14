# Proposed Azure architecture for this POC. This configuration is written
# to be valid and `terraform plan`-able, but it is NOT applied as part of
# this project - see docs/AZURE_ARCHITECTURE.md and docs/SECURITY_AND_COST.md.

locals {
  name_prefix = "${var.project_name}-dev"
}

module "resource_group" {
  source = "../../modules/resource_group"

  name     = "rg-${local.name_prefix}"
  location = var.location
  tags     = var.tags
}

module "log_analytics" {
  source = "../../modules/log_analytics"

  name                = "law-${local.name_prefix}"
  resource_group_name = module.resource_group.name
  location            = var.location
  retention_in_days   = var.log_retention_days
  tags                = var.tags
}

module "acr" {
  source = "../../modules/acr"

  # ACR names must be globally unique and alphanumeric only.
  name                = replace("acr${local.name_prefix}", "-", "")
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

module "key_vault" {
  source = "../../modules/key_vault"

  name                = "kv-${local.name_prefix}"
  resource_group_name = module.resource_group.name
  location            = var.location
  tenant_id           = var.tenant_id
  tags                = var.tags
}

module "aks" {
  source = "../../modules/aks"

  name                       = "aks-${local.name_prefix}"
  resource_group_name        = module.resource_group.name
  location                   = var.location
  dns_prefix                 = local.name_prefix
  node_count                 = var.node_count
  log_analytics_workspace_id = module.log_analytics.workspace_id
  acr_id                     = module.acr.id
  tags                       = var.tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  aks_name                   = module.aks.name
  aks_id                     = module.aks.id
  log_analytics_workspace_id = module.log_analytics.workspace_id
}

# A user-assigned managed identity representing the application workload.
# In a full deployment this would be federated with the AKS OIDC issuer
# (azurerm_federated_identity_credential + a Kubernetes ServiceAccount
# annotation) so a pod can request a Key Vault secret without any stored
# credential. That federation step is intentionally left undone here to
# keep the Terraform surface small - see docs/AZURE_ARCHITECTURE.md.
resource "azurerm_user_assigned_identity" "workload" {
  name                = "id-${local.name_prefix}-workload"
  resource_group_name = module.resource_group.name
  location            = var.location
  tags                = var.tags
}

resource "azurerm_role_assignment" "workload_kv_secrets_user" {
  scope                = module.key_vault.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.workload.principal_id
}
