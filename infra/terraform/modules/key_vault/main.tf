# Key Vault: holds application secrets (e.g. an Azure OpenAI key, if the
# optional AI path were ever enabled in a real deployment). AKS workloads
# would read from it via a managed identity, not a stored credential.

resource "azurerm_key_vault" "this" {
  name                       = var.name
  resource_group_name        = var.resource_group_name
  location                   = var.location
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  purge_protection_enabled   = false # disabled for easy teardown in a non-production POC
  soft_delete_retention_days = 7
  enable_rbac_authorization  = true # access via Azure RBAC role assignments, not legacy access policies
  tags                       = var.tags
}
