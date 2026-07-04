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

See `../_LANG_COMMON.md`. Fetch the truth:

```bash
ruby -v                                                              # local interpreter
cat .ruby-version 2>/dev/null                                        # pin file (if present)
curl -s https://endoflife.date/api/ruby.json | jq -r '.[0].latest'   # latest upstream stable
```

Read `.ruby-version` / `Gemfile` / `<gem>.gemspec` (`required_ruby_version`) for the project's floor.

---

## Pre-Commit Verification (MANDATORY)

`make check && make test-e2e` must pass (enforced by the `pre-commit-gate` hook; see `../_LANG_COMMON.md`). What `make check` expands to for a gem:

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
  spec.required_ruby_version = ">= <current stable minus one>"  # Always specify! Check `ruby -v` / endoflife.date, do not hardcode from memory

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

**RuboCop:** `rubocop-rspec` + `rubocop-performance`, `TargetRubyVersion` set to the gem's `required_ruby_version` floor (do not hardcode from memory), `NewCops: enable`, max line 120, max method 10.

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
| CI | Matrix on the two latest stable Ruby minors (check endoflife.date, do not hardcode), `ruby/setup-ruby`, bundler-cache |

---

## Resources

- [Bundler: Creating Gems](https://bundler.io/guides/creating_gem.html)
- [RubyGems Patterns](https://guides.rubygems.org/patterns/)
- [Ruby version changes](https://rubyreferences.github.io/rubychanges/) (pick the entry for the project's Ruby version)
