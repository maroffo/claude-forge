---
name: ruby
description: "Ruby gem development with modern tooling, testing, and publishing. Use when working with .gemspec, Rakefile, or user asks about gem structure, RSpec for gems, Bundler, or gem publishing. Not for Rails apps (use rails skill)."
compatibility: "Requires Bundler. Optional: RuboCop, SimpleCov."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Ruby gem development guide - structure, testing, linting, CI/CD, publishing
# ABOUTME: Conventions for gemspec, RSpec, RuboCop, publishing with attestation

# Ruby Gem Development

## Quick Reference

```bash
bundle gem my_gem --test=rspec --ci=github --linter=rubocop
bundle install && bundle exec rspec && bundle exec rubocop -A
gem build my_gem.gemspec
gem push my_gem-1.0.0.gem --attestation
```

For Rails apps, use `rails` skill. **See also:** `_AST_GREP.md`, `_PATTERNS.md`, `source-control`

---

## Version (determine, don't assume)

Never assume a Ruby version from prior knowledge: it rots fast and you miss CVE fixes. Fetch the truth:

```bash
ruby -v                                                              # local interpreter
cat .ruby-version 2>/dev/null                                        # pin file (if present)
curl -s https://endoflife.date/api/ruby.json | jq -r '.[0].latest'   # latest upstream stable
```

For a new project, pin to the latest stable. For an existing one, read `.ruby-version` / `Gemfile` / `<gem>.gemspec` (`required_ruby_version`) and prefer idioms gated to that version or lower.

---

## Pre-Commit Verification (MANDATORY)

Before every commit, both of these MUST pass:

```bash
make check       # project-wide gate (lint, tests, security)
make test-e2e    # end-to-end tests (or the project's e2e target)
```

If `make check` is missing, scaffold it with the `project-checks` skill. If there is no e2e target, do NOT silently skip: flag it to the user and ask whether to proceed or add one.

Full raw toolchain (what `make check` should expand to):

```bash
bundle exec rubocop
bundle exec rspec
bundle exec bundler-audit check --update
```

---

## Gem Structure

```
my_gem/
├── lib/my_gem.rb           # Entry point
├── lib/my_gem/version.rb   # VERSION constant
├── spec/                   # RSpec tests
├── sig/                    # RBS types (optional)
├── .github/workflows/ci.yml
├── .rubocop.yml
├── my_gem.gemspec
└── Gemfile
```

### Entry Point (lib/my_gem.rb)

```ruby
# frozen_string_literal: true

# ABOUTME: Main entry point for MyGem
# ABOUTME: Requires all components and provides configuration

require_relative "my_gem/version"
require_relative "my_gem/client"

module MyGem
  class << self
    attr_writer :configuration
    def configuration = @configuration ||= Configuration.new
    def configure = yield(configuration) if block_given?
  end
end
```

---

## Gemspec

```ruby
# frozen_string_literal: true

Gem::Specification.new do |spec|
  spec.name = "my_gem"
  spec.version = MyGem::VERSION
  spec.required_ruby_version = ">= 3.3.0"  # Always specify!

  spec.metadata = {
    "rubygems_mfa_required" => "true",  # Required!
    "source_code_uri" => "https://github.com/you/my_gem",
    "changelog_uri" => "https://github.com/you/my_gem/blob/main/CHANGELOG.md"
  }

  spec.files = Dir.glob(%w[lib/**/* LICENSE.txt README.md CHANGELOG.md])
  # Runtime deps in gemspec, dev deps in Gemfile
end
```

---

## Testing & Quality

**RSpec:** `describe`/`it` with `expect` syntax, `subject(:name)`, WebMock for HTTP, SimpleCov >= 90%.

**RuboCop:** `rubocop-rspec` + `rubocop-performance`, `TargetRubyVersion: 3.3`, `NewCops: enable`, max line 120, max method 10.

**Thread safety:** `Mutex.new` + `@mutex.synchronize { ... }` for shared state.

For detailed testing examples, CI config, HTTP client pattern, and publishing steps, see `references/ruby-patterns.md`.

---

## Code Review Checklist

| Category | Checks |
|----------|--------|
| Structure | `frozen_string_literal`, ABOUTME headers, standard layout |
| Gemspec | `required_ruby_version`, `rubygems_mfa_required`, metadata URIs |
| Testing | RSpec expect syntax, SimpleCov >= 90%, WebMock, no real HTTP |
| Quality | RuboCop passes, thread-safe if async, custom error classes |
| CI | Ruby 3.3+3.4, `ruby/setup-ruby`, bundler-cache |

---

## Resources

- [Bundler: Creating Gems](https://bundler.io/guides/creating_gem.html)
- [RubyGems Patterns](https://guides.rubygems.org/patterns/)
- [Ruby 3.4 Changes](https://rubyreferences.github.io/rubychanges/3.4.html)
