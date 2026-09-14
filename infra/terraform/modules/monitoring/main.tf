# Azure Monitor diagnostic settings: routes AKS control-plane logs and
# platform metrics into the same Log Analytics workspace that Container
# Insights (the cluster's oms_agent addon) already uses. This is what makes
# "Azure Monitor" a distinct, visible piece of the architecture rather than
# an implicit side effect of enabling Container Insights.

resource "azurerm_monitor_diagnostic_setting" "aks" {
  name                       = "${var.aks_name}-diagnostics"
  target_resource_id         = var.aks_id
  log_analytics_workspace_id = var.log_analytics_workspace_id

  enabled_log {
    category = "kube-apiserver"
  }

  enabled_log {
    category = "kube-controller-manager"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}
