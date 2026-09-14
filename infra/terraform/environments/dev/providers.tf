terraform {
  required_version = ">= 1.6"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.116"
    }
  }

  # No backend is configured on purpose: this POC is validated with
  # `terraform init -backend=false` and is never applied. A real deployment
  # would add a remote backend (e.g. an Azure Storage account) here.
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }

  # subscription_id / tenant_id are intentionally not set here - they come
  # from the environment (az login) or CI service connection, never from
  # source control.
}
