# AKS cluster: a small, single-node-pool cluster suitable for a POC
# workload. Uses a system-assigned managed identity (no stored credential),
# is wired to Log Analytics for Container Insights, and is granted
# AcrPull on the registry via Azure RBAC rather than the registry's
# admin account.

resource "azurerm_kubernetes_cluster" "this" {
  name                = var.name
  resource_group_name = var.resource_group_name
  location            = var.location
  dns_prefix          = var.dns_prefix
  kubernetes_version  = var.kubernetes_version

  default_node_pool {
    name       = "system"
    node_count = var.node_count
    vm_size    = var.node_vm_size
  }

  identity {
    type = "SystemAssigned"
  }

  # Minimum-reasonable networking for a POC: kubenet keeps the underlying
  # VNet/subnet requirements small compared to Azure CNI.
  network_profile {
    network_plugin    = "kubenet"
    load_balancer_sku = "standard"
  }

  oms_agent {
    log_analytics_workspace_id = var.log_analytics_workspace_id
  }

  tags = var.tags
}

# Grants the cluster's kubelet identity permission to pull images from ACR,
# instead of embedding a registry credential in a Kubernetes Secret.
resource "azurerm_role_assignment" "acr_pull" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.this.kubelet_identity[0].object_id
}
