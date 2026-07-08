output "vpc_id" {
  description = "ID of the environment's VPC."
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets created for this environment."
  value       = module.network.public_subnet_ids
}

output "managed_nodes_security_group_id" {
  description = "Security group ID applied to nodes managed by this framework."
  value       = aws_security_group.managed_nodes.id
}
