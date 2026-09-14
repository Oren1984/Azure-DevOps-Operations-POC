variable "name" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "dns_prefix" {
  type = string
}

variable "kubernetes_version" {
  description = "Pin explicitly in a real deployment; left null here to track AKS's current default."
  type        = string
  default     = null
}

variable "node_count" {
  description = "Kept at 1 by default to minimize POC cost. Increase for real availability needs."
  type        = number
  default     = 1
}

variable "node_vm_size" {
  description = "Small burstable SKU, adequate for a lightweight POC workload."
  type        = string
  default     = "Standard_B2s"
}

variable "log_analytics_workspace_id" {
  description = "Workspace the Container Insights (oms_agent) addon sends cluster logs and metrics to."
  type        = string
}

variable "acr_id" {
  description = "ACR resource ID the cluster's kubelet identity is granted AcrPull on."
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
