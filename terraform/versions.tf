terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.55"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state backend. Left commented/partial so environments can supply
  # the remaining values with `terraform init -backend-config=...` (see
  # environments/<env>/ for per-environment values). The iac_framework
  # TerraformRunner.init() method accepts backend_config overrides for
  # exactly this purpose.
  # backend "s3" {
  #   bucket         = "REPLACE_WITH_STATE_BUCKET"
  #   key            = "infrastructure-automation-framework/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-locks"
  #   encrypt        = true
  # }
}
