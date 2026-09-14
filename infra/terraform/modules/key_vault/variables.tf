variable "name" {
  description = "Globally-unique Key Vault name."
  type        = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "tenant_id" {
  description = "Microsoft Entra ID tenant ID. Never hardcode this - pass it in at apply time."
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
