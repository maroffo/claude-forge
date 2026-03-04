# ABOUTME: Detailed Ruby gem patterns for CI, testing, HTTP clients, and publishing
# ABOUTME: Reference companion to ruby SKILL.md with full code examples

# Ruby Gem Patterns

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

## Testing (RSpec)

### spec_helper.rb

```ruby
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

### Client Spec Example

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

## HTTP Client (stdlib)

Pattern: `Net::HTTP` + `JSON.parse`, set `use_ssl`, `open_timeout`, `read_timeout`. Auth via `request["Authorization"] = "Bearer #{@token}"`. Keep client class with `initialize(base_url:, token:, timeout:)` + private `execute(request)` method.

---

## Publishing

```bash
bundle exec rspec && bundle exec rubocop && gem build my_gem.gemspec
gem install ./my_gem-X.Y.Z.gem    # Test locally
gem push my_gem-X.Y.Z.gem --attestation && bundle lock --add-checksums
```
