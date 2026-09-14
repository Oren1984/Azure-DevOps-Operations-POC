variable "name" {
  description = "Globally-unique ACR name (alphanumeric only)."
  type        = string
}

variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "sku" {
  description = "Basic is the lowest-cost tier and is sufficient for a POC."
  type        = string
  default     = "Basic"
}

variable "tags" {
  type    = map(string)
  default = {}
}
