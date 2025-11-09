---
name: terraform
description: "Terraform and Terragrunt for infrastructure as code. Use for IaC, modules, state management, HCL."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Terraform and Terragrunt infrastructure as code patterns
# ABOUTME: Module design, state management, DRY configurations, best practices

# Terraform & Terragrunt

## Quick Reference

```bash
# Terraform basics
terraform init
terraform plan
terraform apply
terraform destroy

# Terragrunt
terragrunt init
terragrunt plan
terragrunt apply
terragrunt run-all apply

# Format & validate
terraform fmt -recursive
terraform validate

# State management
terraform state list
terraform state show <resource>
terraform state rm <resource>
terraform import <resource> <id>

# Workspaces
terraform workspace list
terraform workspace select <name>
terraform workspace new <name>
```

**Common patterns (ast-grep):**
```bash
sg --pattern 'resource "$TYPE" "$NAME" { $$$ }' --lang hcl
sg --pattern 'module "$NAME" { $$$ }' --lang hcl
sg --pattern 'variable "$NAME" { $$$ }' --lang hcl
sg --pattern 'output "$NAME" { $$$ }' --lang hcl
```

**See also:**
- Code search: `_AST_GREP.md`
- Patterns: `_PATTERNS.md`
- Git: `source-control`

---

## § Terraform Basics

### Project Structure

**Simple project:**
```
terraform/
├── main.tf           # Primary resources
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── versions.tf       # Provider versions
└── terraform.tfvars  # Variable values (gitignored if sensitive)
```

**Multi-environment:**
```
terraform/
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── eks/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   └── prod/
└── README.md
```

### Basic Syntax

**Resources:**
```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"

  tags = {
    Name        = "web-server"
    Environment = var.environment
  }
}
```

**Variables:**
```hcl
variable "environment" {
  description = "Environment name"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod"
  }
}

variable "instance_count" {
  description = "Number of instances"
  type        = number
  default     = 1
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
```

**Outputs:**
```hcl
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web.id
}

output "public_ip" {
  description = "Public IP of instance"
  value       = aws_instance.web.public_ip
  sensitive   = false
}
```

**Data sources:**
```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }
}
```

### Providers

```hcl
terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "my-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}
```

---

## § Module Design

### Module Structure

```
modules/vpc/
├── main.tf           # Primary resources
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── versions.tf       # Provider requirements
└── README.md         # Module documentation
```

### Module Example

**modules/vpc/main.tf:**
```hcl
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    var.tags,
    {
      Name = var.vpc_name
    }
  )
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(
    var.tags,
    {
      Name = "${var.vpc_name}-public-${count.index + 1}"
      Type = "public"
    }
  )
}
```

**modules/vpc/variables.tf:**
```hcl
variable "vpc_name" {
  description = "Name of the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "public_subnet_cidrs" {
  description = "List of public subnet CIDRs"
  type        = list(string)
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

**modules/vpc/outputs.tf:**
```hcl
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = aws_subnet.public[*].id
}
```

### Using Modules

```hcl
module "vpc" {
  source = "./modules/vpc"

  vpc_name             = "prod-vpc"
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  availability_zones   = ["us-east-1a", "us-east-1b"]

  tags = {
    Environment = "production"
    Team        = "platform"
  }
}

# Reference module outputs
resource "aws_instance" "web" {
  subnet_id = module.vpc.public_subnet_ids[0]
  # ...
}
```

---

## § Terragrunt Patterns

### Why Terragrunt?

- **DRY configurations**: Avoid repeating backend/provider config
- **Multiple environments**: Easy management of dev/staging/prod
- **Dependencies**: Manage dependencies between modules
- **Remote state**: Automatic backend configuration

### Directory Structure

```
infrastructure/
├── terragrunt.hcl    # Root configuration
├── dev/
│   ├── terragrunt.hcl
│   ├── vpc/
│   │   └── terragrunt.hcl
│   └── eks/
│       └── terragrunt.hcl
├── staging/
│   ├── terragrunt.hcl
│   ├── vpc/
│   │   └── terragrunt.hcl
│   └── eks/
│       └── terragrunt.hcl
└── prod/
    ├── terragrunt.hcl
    ├── vpc/
    │   └── terragrunt.hcl
    └── eks/
        └── terragrunt.hcl
```

### Root terragrunt.hcl

```hcl
# infrastructure/terragrunt.hcl
remote_state {
  backend = "s3"
  
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
  
  config = {
    bucket         = "my-terraform-state-${get_aws_account_id()}"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  
  contents = <<EOF
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      ManagedBy   = "Terraform"
      Environment = var.environment
    }
  }
}
EOF
}
```

### Environment terragrunt.hcl

```hcl
# infrastructure/prod/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

locals {
  environment = "prod"
  aws_region  = "us-east-1"
}

inputs = {
  environment = local.environment
  aws_region  = local.aws_region
}
```

### Module terragrunt.hcl

```hcl
# infrastructure/prod/vpc/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

include "env" {
  path = find_in_parent_folders("terragrunt.hcl")
}

terraform {
  source = "../../../modules//vpc"
}

inputs = {
  vpc_name            = "prod-vpc"
  vpc_cidr            = "10.0.0.0/16"
  public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
  availability_zones  = ["us-east-1a", "us-east-1b"]
}
```

### Dependencies

```hcl
# infrastructure/prod/eks/terragrunt.hcl
include "root" {
  path = find_in_parent_folders()
}

terraform {
  source = "../../../modules//eks"
}

dependency "vpc" {
  config_path = "../vpc"
}

inputs = {
  vpc_id     = dependency.vpc.outputs.vpc_id
  subnet_ids = dependency.vpc.outputs.public_subnet_ids
}
```

### Terragrunt Commands

```bash
# Single module
cd infrastructure/prod/vpc
terragrunt init
terragrunt plan
terragrunt apply

# All modules in environment
cd infrastructure/prod
terragrunt run-all init
terragrunt run-all plan
terragrunt run-all apply

# With dependency order
terragrunt run-all apply --terragrunt-non-interactive
```

---

## § State Management

### Remote State

**S3 backend (recommended for AWS):**
```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### State Commands

```bash
# List resources
terraform state list

# Show resource details
terraform state show aws_instance.web

# Move resource
terraform state mv aws_instance.web aws_instance.web_server

# Remove from state (doesn't destroy)
terraform state rm aws_instance.web

# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Pull remote state
terraform state pull > terraform.tfstate.backup
```

### State Locking

**DynamoDB table for S3 backend:**
```hcl
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = "Terraform State Lock Table"
  }
}
```

---

## § Best Practices

### Code Organization

**✅ DO:**
- Use modules for reusable components
- Keep resources in logical files (networking.tf, compute.tf, etc.)
- Use consistent naming conventions
- Document modules with README
- Version your modules
- Use workspaces OR directories for environments (not both)

**❌ DON'T:**
- Put everything in one file
- Hardcode values (use variables)
- Commit `.tfstate` files to git
- Share state files between environments
- Use count/for_each for environment logic

### Naming Conventions

```hcl
# Resources: type_description
resource "aws_instance" "web_server" { }
resource "aws_security_group" "web_sg" { }

# Variables: descriptive_name
variable "instance_type" { }
variable "vpc_cidr_block" { }

# Modules: functional_name
module "vpc" { }
module "database" { }
```

### Security

**✅ DO:**
- Use remote state with encryption
- Enable state locking
- Use `.gitignore` for sensitive files
- Use AWS Secrets Manager/Parameter Store for secrets
- Rotate credentials regularly
- Use IAM roles, not access keys

**Sensitive data:**
```hcl
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

output "db_endpoint" {
  value     = aws_db_instance.main.endpoint
  sensitive = true
}
```

### .gitignore

```gitignore
# Terraform
.terraform/
*.tfstate
*.tfstate.*
*.tfvars
.terragrunt-cache/
crash.log
override.tf
override.tf.json

# Sensitive
*.pem
*.key
secrets.tf
```

---

## § Common Patterns

### For Each vs Count

**Use for_each for maps:**
```hcl
variable "instances" {
  type = map(object({
    instance_type = string
    ami           = string
  }))
}

resource "aws_instance" "servers" {
  for_each = var.instances

  instance_type = each.value.instance_type
  ami           = each.value.ami

  tags = {
    Name = each.key
  }
}
```

**Use count for simple lists:**
```hcl
resource "aws_subnet" "public" {
  count  = length(var.public_subnet_cidrs)
  vpc_id = aws_vpc.main.id

  cidr_block        = var.public_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]
}
```

### Dynamic Blocks

```hcl
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = var.vpc_id

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }
}
```

### Conditionals

```hcl
resource "aws_instance" "web" {
  count = var.create_instance ? 1 : 0

  ami           = var.ami
  instance_type = var.instance_type
}

# Better: use for_each with conditional map
resource "aws_instance" "web" {
  for_each = var.create_instance ? { main = true } : {}

  ami           = var.ami
  instance_type = var.instance_type
}
```

---

## § Testing

### terraform fmt

```bash
# Format all files
terraform fmt -recursive

# Check formatting (CI)
terraform fmt -check -recursive
```

### terraform validate

```bash
terraform validate
```

### terraform plan

```bash
# Always review plan
terraform plan -out=tfplan

# Apply the plan
terraform apply tfplan
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running Terraform checks..."

# Format
terraform fmt -recursive -check
if [ $? -ne 0 ]; then
    echo "Format failed. Run: terraform fmt -recursive"
    exit 1
fi

# Validate
terraform validate
if [ $? -ne 0 ]; then
    echo "Validation failed"
    exit 1
fi

echo "✓ Terraform checks passed"
```

---

## § Troubleshooting

### Common Issues

**State locked:**
```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

**Resource already exists:**
```bash
# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0
```

**Drift detection:**
```bash
# Show differences between state and reality
terraform plan -refresh-only
```

**Debugging:**
```bash
# Enable debug logging
export TF_LOG=DEBUG
export TF_LOG_PATH=terraform.log

terraform apply
```

---

## § Resources

**Official:**
- https://www.terraform.io/docs
- https://terragrunt.gruntwork.io/docs/

**Tools:**
- terraform-docs: Generate documentation
- tflint: Linter for Terraform
- checkov: Security scanner
- infracost: Cost estimation

**Related Skills:**
- Code search: `_AST_GREP.md`
- Git: `source-control`

---

**End of SKILL: Terraform & Terragrunt**
