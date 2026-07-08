# Example root module managed by the iac_framework orchestrator.
#
# This models a minimal environment: a VPC with public subnets (via the
# network module) plus a placeholder compute resource. Real deployments
# would extend this with additional modules (e.g. compute, database)
# following the same pattern as `modules/network`.

module "network" {
  source = "./modules/network"

  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  tags               = var.tags
}

resource "random_id" "suffix" {
  byte_length = 2
}

# Placeholder compute resource wired to the network module's output. In a
# real environment this would be an aws_instance, aws_autoscaling_group, or
# similar; kept minimal here so `terraform validate` succeeds without
# requiring an AMI lookup or live AWS credentials.
resource "aws_security_group" "managed_nodes" {
  name_prefix = "${var.environment}-iac-fw-${random_id.suffix.hex}-"
  description = "Security group for nodes managed by iac_framework in ${var.environment}."
  vpc_id      = module.network.vpc_id

  egress {
    description = "Allow all outbound traffic."
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow SSH from within the VPC."
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = merge(var.tags, {
    Name = "${var.environment}-iac-fw-managed-nodes"
  })
}
