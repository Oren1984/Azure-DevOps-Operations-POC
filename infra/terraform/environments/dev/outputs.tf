output "resource_group_name" {
  value = module.resource_group.name
}

output "acr_login_server" {
  value = module.acr.login_server
}

output "aks_cluster_name" {
  value = module.aks.name
}

output "key_vault_uri" {
  value = module.key_vault.vault_uri
}

output "log_analytics_workspace_name" {
  value = module.log_analytics.workspace_name
}

output "workload_identity_client_id" {
  value = azurerm_user_assigned_identity.workload.client_id
}
