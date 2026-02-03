---
name: ruby
description: "Ruby gem development with modern tooling, testing, and publishing best practices."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Ruby gem development guide - structure, testing, linting, CI/CD, publishing
# ABOUTME: Modern Ruby (3.3-3.4): Prism parser, frozen strings, Ractor, attestation

# Ruby Gem Development

## What's New (2025-2026)

| Ruby 3.4 | RubyGems 4.0 |
|----------|--------------|
| Prism default parser | Go extension support |
| Frozen string warnings | 5 parallel connections |
| Gem attestation (sigstore) | Reproducible builds |
| Bundler checksums | |
| Ractor require | |

## Quick Reference

```bash
bundle gem my_gem --test=rspec --ci=github --linter=rubocop
bundle install && bundle exec rspec && bundle exec rubocop -A
gem build my_gem.gemspec
gem push my_gem-1.0.0.gem --attestation
```

**Target: Ruby 3.3+** | For Rails apps → use `rails` skill

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

## Testing (RSpec)

```ruby
# spec/spec_helper.rb
require "simplecov"
SimpleCov.start { minimum_coverage 90 }
require "my_gem"
require "webmock/rspec"

RSpec.configure do |config|
  config.disable_monkey_patching!
  config.expect_with(:rspec) { |c| c.syntax = :expect }
  WebMock.disable_net_connect!(allow_localhost: true)
end
```

```ruby
# spec/my_gem/client_spec.rb
RSpec.describe MyGem::Client do
  subject(:client) { described_class.new(token: "test") }

  describe "#get" do
    before do
      stub_request(:get, "https://api.example.com/data")
        .to_return(status: 200, body: '{"id": 1}')
    end

    it "returns parsed JSON" do
      expect(client.get("/data")).to eq({ "id" => 1 })
    end
  end
end
```

---

## RuboCop

```yaml
# .rubocop.yml
require: [rubocop-rspec, rubocop-performance]

AllCops:
  TargetRubyVersion: 3.3
  NewCops: enable

Style/FrozenStringLiteralComment:
  EnforcedStyle: always

Layout/LineLength:
  Max: 120

Metrics/MethodLength:
  Max: 10
```

---

## CI (GitHub Actions)

```yaml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with: { ruby-version: "3.3", bundler-cache: true }
      - run: bundle exec rubocop

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        ruby-version: ["3.3", "3.4"]
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with: { ruby-version: "${{ matrix.ruby-version }}", bundler-cache: true }
      - run: bundle exec rspec
```

---

## Thread Safety

```ruby
# frozen_string_literal: true

module MyGem
  class Queue
    def initialize(max_size:)
      @items, @mutex = [], Mutex.new
      @max_size = max_size
    end

    def push(item)
      @mutex.synchronize { @items << item if @items.size < @max_size }
    end

    def pop
      @mutex.synchronize { @items.shift }
    end
  end
end
```

---

## HTTP Client (stdlib)

```ruby
# frozen_string_literal: true

require "net/http"
require "json"

module MyGem
  class Client
    def initialize(base_url:, token:, timeout: 10)
      @uri = URI.parse(base_url)
      @token, @timeout = token, timeout
    end

    def get(path)
      request = Net::HTTP::Get.new(path)
      execute(request)
    end

    private

    def execute(request)
      request["Authorization"] = "Bearer #{@token}"
      http = Net::HTTP.new(@uri.host, @uri.port)
      http.use_ssl = @uri.scheme == "https"
      http.open_timeout = http.read_timeout = @timeout
      JSON.parse(http.request(request).body)
    end
  end
end
```

---

## Publishing

```bash
# Pre-release
bundle exec rspec && bundle exec rubocop
gem build my_gem.gemspec
gem install ./my_gem-X.Y.Z.gem  # Test locally

# Publish
gem push my_gem-1.0.0.gem --attestation
bundle lock --add-checksums  # Supply chain security
```

---

## Code Review Checklist

| Category | Checks |
|----------|--------|
| Structure | `frozen_string_literal`, ABOUTME headers, standard layout |
| Gemspec | `required_ruby_version`, `rubygems_mfa_required`, metadata URIs |
| Testing | RSpec expect syntax, SimpleCov ≥90%, WebMock, no real HTTP |
| Quality | RuboCop passes, thread-safe if async, custom error classes |
| CI | Ruby 3.3+3.4, `ruby/setup-ruby`, bundler-cache |

---

## ast-grep Patterns

```bash
sg --pattern 'class $NAME' --lang ruby
sg --pattern 'def $NAME($$$)' --lang ruby
sg --pattern 'require $PATH' --lang ruby
sg --pattern 'rescue $TYPE => $VAR' --lang ruby
```

---

## Resources

- [Bundler: Creating Gems](https://bundler.io/guides/creating_gem.html)
- [RubyGems Patterns](https://guides.rubygems.org/patterns/)
- [Ruby 3.4 Changes](https://rubyreferences.github.io/rubychanges/3.4.html)
