# Log Analytics Workspace: the central store AKS Container Insights, Azure
# Monitor, and Application Insights all write into. See
# docs/AZURE_ARCHITECTURE.md for how these pieces connect.

resource "azurerm_log_analytics_workspace" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = var.retention_in_days
  tags                = var.tags
}

# Workspace-based Application Insights: application-level telemetry
# (requests, dependencies, exceptions) that also lands in the same
# Log Analytics workspace as the AKS cluster's own logs.
resource "azurerm_application_insights" "this" {
  name                = "${var.name}-appi"
  resource_group_name = var.resource_group_name
  location            = var.location
  workspace_id        = azurerm_log_analytics_workspace.this.id
  application_type    = "web"
  tags                = var.tags
}
