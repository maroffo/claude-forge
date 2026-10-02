---
name: terraform
description: "Terraform and Terragrunt for infrastructure as code. Use for IaC, modules, state management, HCL."
compatibility: "Requires terraform CLI. Optional: tflint, checkov, infracost."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Terraform/Terragrunt IaC patterns, modules, state management
# ABOUTME: Best practices for HCL, DRY configs, security scanning

# Terraform & Terragrunt

**OpenTofu**: open-source (MPL) fork, recommended for new projects because Terraform is BSL-licensed. The two have diverged since the fork, so check feature parity against the version the project runs.

## Quick Reference

```bash
terraform init|plan|apply|destroy
terragrunt run --all apply
terraform fmt -recursive && terraform validate
terraform state list|show|rm|mv <resource>
```

**See:** `_AST_GREP.md` (sg patterns for HCL)

---

## Project Structure

**Simple:** `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`

**Multi-env:**
```
terraform/
├── modules/{vpc,eks}/
└── environments/{dev,staging,prod}/
```

## TF 1.5+ Blocks

```hcl
import { to = aws_instance.web; id = "i-1234567890abcdef0" }
moved { from = aws_instance.web; to = module.web.aws_instance.main }
check "health" {
  data "http" "api" { url = "https://api.example.com/health" }
  assert { condition = data.http.api.status_code == 200; error_message = "API down" }
}
```

---

## Terragrunt

**Benefits:** DRY configs, multi-env mgmt, dependency ordering, auto backend config

### Structure
```
infrastructure/
├── terragrunt.hcl           # Root
├── _envcommon/{vpc,eks}.hcl
├── {dev,staging,prod}/
│   └── {region}/{vpc,eks}/terragrunt.hcl
```

### Dependencies
```hcl
dependency "vpc" { config_path = "../vpc" }
inputs = { vpc_id = dependency.vpc.outputs.vpc_id }
```

---

## State Management

**Split by:** env, region, component, blast radius

```hcl
backend "s3" { bucket = "my-state"; key = "prod/terraform.tfstate"; encrypt = true; use_lockfile = true }  # S3-native locking; dynamodb_table only on versions without it
```

---

## Testing & Security

**Pipeline:** `fmt/validate` → `TFLint` → `Checkov/Trivy` → `Infracost`

```bash
terraform fmt -check -recursive && terraform validate
tflint --recursive
checkov -d . --framework terraform --compact
infracost breakdown --path .
```

---

## Code Review Checklist

**Security:** No hardcoded secrets, encrypted state, locking enabled, least-privilege IAM, Checkov passes

**Structure:** Versioned modules, validated variables, consistent naming

---

## Resources

| Tool | Purpose |
|------|---------|
| TFLint | Linter |
| Checkov | Security |
| Infracost | Cost estimation |

**Docs:** [Terraform](https://terraform.io/docs), [OpenTofu](https://opentofu.org/docs/), [Terragrunt](https://terragrunt.gruntwork.io/docs/)
