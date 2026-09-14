variable "name" {
  description = "Base name for the Log Analytics workspace (Application Insights is derived from it)."
  type        = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "retention_in_days" {
  description = "Log retention. Kept short by default to limit POC cost if ever deployed."
  type        = number
  default     = 30
}

variable "tags" {
  type    = map(string)
  default = {}
}
