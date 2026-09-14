variable "project_name" {
  description = "Short name used as a prefix for every resource."
  type        = string
  default     = "adops-poc"
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "westeurope"
}

variable "tenant_id" {
  description = "Microsoft Entra ID tenant ID for Key Vault. Never hardcode a real value; pass via -var or TF_VAR_tenant_id."
  type        = string
  default     = "00000000-0000-0000-0000-000000000000"
}

variable "node_count" {
  description = "AKS node count. Kept at 1 by default to minimize POC cost."
  type        = number
  default     = 1
}

variable "log_retention_days" {
  type    = number
  default = 30
}

variable "tags" {
  type = map(string)
  default = {
    project     = "azure-devops-operations-poc"
    environment = "dev"
    managed_by  = "terraform"
  }
}
