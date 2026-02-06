---
name: rails
description: "Ruby on Rails 8 with service-oriented architecture, Dry-validation, Sidekiq/Solid Queue, Hotwire. Use for Rails API, Rails services, Rails forms, RSpec, ActiveRecord, Rails migrations."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Rails 8 service-oriented architecture, validation contracts, background jobs, Hotwire
# ABOUTME: API development with thin controllers, services, forms, filters, and modern Rails stack

# Ruby on Rails - Modern Development

## Quick Reference

```bash
bundle exec lefthook run all    # Quality checks
bundle exec rspec               # Tests
rails s / bin/dev               # Server (bin/dev for Hotwire)
bin/jobs                        # Solid Queue workers
```

**See also:** `_AST_GREP.md` (sg patterns), `_PATTERNS.md`, `source-control`

**Architecture calls:**
```ruby
MyService.new(user:, params:).call    # Service
MyForm.new(params, user).save         # Form
MyFilter.result(params, scope)        # Filter
MyJob.perform_async(id)               # Sidekiq
MyJob.perform_later(id)               # Solid Queue
```

---

## Sacred Rules (NON-NEGOTIABLE)

1. **NO LOGIC IN CONTROLLERS** - HTTP layer only
2. **ALL LOGIC IN SERVICES/FORMS/FILTERS**
3. **NO ACTIVERECORD VALIDATIONS** - Dry-validation contracts only
4. **MINIMUM MODEL LOGIC** - Data structures + associations
5. **NO MODEL CALLBACKS** - Exception: attachment destruction

---

## Ruby 3.4 & Rails 8

**YJIT enabled by default** (15-30% faster). New `it` block parameter:
```ruby
users.map { it.name }  # replaces _1
```

**Solid Trifecta** (DB-backed alternatives to Redis):
| Component | Purpose | Use When |
|-----------|---------|----------|
| Solid Queue | Jobs | <100 jobs/sec, no Redis needed |
| Solid Cache | Caching | 10TB+ possible |
| Solid Cable | WebSockets | No Redis infra |

**Use Sidekiq when:** latency <100ms required, 10k+ jobs/min

---

## Service Pattern

```ruby
module Feature
  class OperationService
    def initialize(user:, params:)
      @user, @params = user, params
    end

    def call
      validate_preconditions
      ActiveRecord::Base.transaction { perform_operation }
      schedule_jobs  # AFTER transaction
      OpenStruct.new(success: true, record: @record)
    end

    private

    def validate_preconditions
      raise UnauthorizedError unless @user.can_perform?
    end

    def perform_operation
      @record = @user.records.create!(name: @params[:name])
    end

    def schedule_jobs
      ProcessJob.perform_async(@record.id)
    end
  end
end
```

---

## Form & Contract Pattern

```ruby
# Contract = validation rules
class CreateContract < Dry::Validation::Contract
  params do
    required(:name).filled(:string, max_size?: 255)
    optional(:category_id).filled(:integer)
  end

  rule(:name) do
    key.failure(I18n.t('errors.messages.taken')) if Feature.exists?(name: value.downcase)
  end
end

# Form = orchestrate + persist
class CreateForm < BaseForm
  def initialize(attributes, current_user)
    super(attributes)
    @current_user = current_user
    @contract = CreateContract.new
  end

  private

  def persist!
    ActiveRecord::Base.transaction do
      @model = Feature.create!(validated_params.merge(user: @current_user))
    end
    ProcessJob.perform_async(@model.id)
  end
end
```

---

## Controller Pattern

Controllers = HTTP layer ONLY.

```ruby
class FeaturesController < Api::V1::BaseController
  def index = render(json: FeaturesFilter.result(filter_params, current_user.features))

  def create
    form = CreateForm.new(feature_params, current_user)
    form.save ? render(json: form.model, status: :created) : render(json: { errors: form.errors }, status: :unprocessable_entity)
  end
end
```

---

## Model Pattern

Models = associations + enums + simple scopes. NO validation, NO callbacks, NO business logic.

```ruby
class Feature < ApplicationRecord
  belongs_to :user
  has_many :tags, dependent: :destroy
  enum :status, { draft: 0, published: 1, archived: 2 }
  scope :recent, -> { order(created_at: :desc) }
end
```

---

## Background Jobs

**Sidekiq:**
```ruby
class ProcessJob
  include Sidekiq::Job
  sidekiq_options retry: 3, queue: :default

  def perform(feature_id)
    Feature.find(feature_id).then { ProcessService.new(feature: _1).call }
  rescue ActiveRecord::RecordNotFound => e
    Rails.logger.error("Feature ##{feature_id} not found")
  end
end
```

---

## Hotwire

**Turbo Frames:**
```erb
<%= turbo_frame_tag "list" do %><% @items.each { |i| render i } %><% end %>
<%= link_to "Filter", path, data: { turbo_frame: "list" } %>
```

**Turbo Streams:** `append`, `prepend`, `replace`, `update`, `remove`

**Stimulus:**
```javascript
export default class extends Controller {
  static targets = ["source"]
  copy() { navigator.clipboard.writeText(this.sourceTarget.value) }
}
```

---

## Testing

```ruby
factory :feature do
  user
  sequence(:name) { "Feature #{_1}" }
  trait(:published) { status { :published } }
end

# Performance: build_stubbed > build > create
let(:user) { build_stubbed(:user) }

describe '#call' do
  it 'creates feature' do
    expect { service.call }.to change(Feature, :count).by(1)
  end
end
```

---

## Quality Checklist

Before commit: `bundle exec lefthook run all`

- [ ] NO controller logic
- [ ] Validation in contracts only
- [ ] Business logic in services
- [ ] Jobs idempotent
- [ ] Tests pass

---

## Resources

- https://guides.rubyonrails.org/
- https://dry-rb.org/gems/dry-validation/
- https://github.com/rails/solid_queue
- https://turbo.hotwired.dev/

**Key gems:** Dry-validation, Sidekiq/Solid Queue, Scenic, Pundit, Devise/Rodauth, ViewComponent/Phlex
