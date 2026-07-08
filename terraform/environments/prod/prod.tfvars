aws_region         = "us-east-1"
environment        = "prod"
vpc_cidr           = "10.1.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
instance_type      = "m6i.large"

tags = {
  Project     = "infrastructure-automation-framework"
  Environment = "prod"
  Owner       = "platform-team"
}
