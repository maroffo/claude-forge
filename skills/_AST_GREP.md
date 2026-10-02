# ABOUTME: ast-grep universal guide for AST-aware code search across all languages
# ABOUTME: Use ast-grep instead of grep/ripgrep when searching code

# ast-grep (sg) - Universal Code Search

## Default for code search

Use `ast-grep` (`sg`) to search code: it matches syntax, so hits inside comments and strings do not show up as false positives. For non-code files, paths, and prose, use grep or ripgrep (see When NOT to use ast-grep).

## Why ast-grep?

- **AST-aware**: Matches code structure, not text
- **No false positives**: Ignores comments, strings, docstrings
- **Language-native**: Understands syntax semantically
- **Refactoring-safe**: Structural matching guarantees correctness

## Installation Check

```bash
sg --version  # Verify ast-grep is installed
```

## Pattern Syntax

```
$VAR        Match single identifier
$$$         Match multiple items (variadic)
$$          Match optional item
$_          Match anything (wildcard)
```

## Universal Flags

```bash
--lang LANG    Specify language (go, python, ruby, hcl, rust, etc.)
--pattern PAT  Search pattern
-A N           Show N lines after match
-B N           Show N lines before match
-C N           Show N lines before and after
```

## Go Patterns

```bash
# Functions
sg --pattern 'func $NAME($$$) $$$' --lang go

# Structs
sg --pattern 'type $NAME struct { $$$ }' --lang go

# Interfaces
sg --pattern 'type $NAME interface { $$$ }' --lang go

# Error handling
sg --pattern 'if err != nil { $$$ }' --lang go

# Ignored errors (anti-pattern)
sg --pattern '$VAR, _ := $EXPR' --lang go

# Goroutines
sg --pattern 'go $FUNC($$$)' --lang go

# Defer
sg --pattern 'defer $FUNC($$$)' --lang go

# Mutex operations
sg --pattern '$VAR.Lock()' --lang go
sg --pattern '$VAR.Unlock()' --lang go
```

## Python Patterns

```bash
# Functions
sg --pattern 'def $NAME($$$): $$$' --lang python

# Async functions
sg --pattern 'async def $NAME($$$): $$$' --lang python

# Classes
sg --pattern 'class $NAME: $$$' --lang python
sg --pattern 'class $NAME($BASE): $$$' --lang python

# Type hints
sg --pattern 'def $NAME($$$) -> $TYPE: $$$' --lang python

# Decorators (multi-line patterns need real newlines: bash $'...' quoting)
sg --pattern $'@$DECORATOR\ndef $NAME($$$):\n    $$$' --lang python

# Exception handling
sg --pattern $'try:\n    $$$\nexcept $EXC:\n    $$$' --lang python

# Imports
sg --pattern 'from $MODULE import $$$' --lang python
sg --pattern 'import $MODULE' --lang python
```

## Ruby Patterns

```bash
# Classes (also matches subclasses)
sg --pattern 'class $NAME' --lang ruby

# Modules
sg --pattern 'module $NAME' --lang ruby

# Methods
sg --pattern 'def $NAME($$$)' --lang ruby

# Service calls
sg --pattern '$SERVICE.call($$$)' --lang ruby

# Background jobs
sg --pattern 'perform_async($$$)' --lang ruby

# ActiveRecord queries
sg --pattern '$MODEL.where($$$)' --lang ruby

# Validations
sg --pattern 'required(:$FIELD)' --lang ruby
```

## HCL/Terraform Patterns

```bash
# Resources
sg --pattern 'resource "$TYPE" "$NAME" { $$$ }' --lang hcl

# Data sources
sg --pattern 'data "$TYPE" "$NAME" { $$$ }' --lang hcl

# Variables
sg --pattern 'variable "$NAME" { $$$ }' --lang hcl

# Outputs
sg --pattern 'output "$NAME" { $$$ }' --lang hcl

# Modules
sg --pattern 'module "$NAME" { $$$ }' --lang hcl
```

## Common Workflows

### Find all TODOs
ast-grep does not match comments, so use ripgrep:
```bash
rg -n 'TODO' --type go --type py --type ruby
```

### Find security issues
```bash
# SQL injection risks (Go)
sg --pattern 'db.Query($QUERY + $VAR)' --lang go

# Eval usage (Python)
sg --pattern 'eval($$$)' --lang python

# Dangerous mass assignment (Rails)
sg --pattern '.create(params)' --lang ruby
```

### Find performance issues
```bash
# N+1 queries (Rails)
sg --pattern '.each do |$VAR| $VAR.$ASSOC' --lang ruby

# Goroutine leaks (Go)
sg --pattern 'go func() { for { $$$ } }()' --lang go
```

## Tips

1. **Start specific, broaden if needed**: Specific patterns are faster
2. **Use context flags (-A, -B, -C)**: See surrounding code
3. **Combine with other tools**: Pipe to grep, wc, etc.
4. **Test patterns**: Verify on known matches first
5. **Escape when needed**: Some chars need escaping in shell

## When NOT to use ast-grep

- Searching in non-code files (logs, config, markdown) → use grep
- Searching across file paths → use find or glob
- Full-text search in docs → use grep or ripgrep

---

**For language-specific patterns, see:**
- Go: `golang/SKILL.md`
- Python: `python/SKILL.md`
- Ruby: `rails/SKILL.md`
- Terraform: `terraform/SKILL.md`
