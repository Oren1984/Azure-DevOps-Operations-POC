# Azure Container Registry: stores the built application image before it is
# pulled by AKS. See docs/AZURE_ARCHITECTURE.md for the build -> push -> pull flow.

resource "azurerm_container_registry" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku
  admin_enabled       = false # authentication is via managed identity + RBAC, not the admin account
  tags                = var.tags
}
