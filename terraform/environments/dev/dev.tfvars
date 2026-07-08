aws_region         = "us-east-1"
environment        = "dev"
vpc_cidr           = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]
instance_type      = "t3.micro"

tags = {
  Project     = "infrastructure-automation-framework"
  Environment = "dev"
  Owner       = "platform-team"
}
