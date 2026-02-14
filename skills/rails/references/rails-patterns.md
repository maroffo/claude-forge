# Rails Pattern Details

Comprehensive examples for service-oriented Rails architecture.

---

## Service Pattern (Full Example)

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

**Key principles:**
- Initialize with dependencies (user, params)
- `call` orchestrates workflow
- Validate preconditions before transaction
- Schedule jobs AFTER transaction commits
- Return structured result (OpenStruct)

---

## Form & Contract Pattern (Full Example)

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

**Key principles:**
- Contract handles validation only
- Form orchestrates persistence
- Use `rule` blocks for custom validation (DB checks, business rules)
- Forms inject additional context (current_user, etc.)
- Jobs scheduled after persistence

---

## Controller Pattern (Full Example)

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

**Allowed in controllers:**
- Parameter whitelisting
- Render decisions
- Status codes
- Delegate to services/forms/filters

**FORBIDDEN in controllers:**
- ActiveRecord queries (except simple `find`)
- Business logic
- Validation
- Transaction management

---

## Model Pattern (Full Example)

Models = associations + enums + simple scopes. NO validation, NO callbacks, NO business logic.

```ruby
class Feature < ApplicationRecord
  belongs_to :user
  has_many :tags, dependent: :destroy
  enum :status, { draft: 0, published: 1, archived: 2 }
  scope :recent, -> { order(created_at: :desc) }
end
```

**Allowed in models:**
- Associations (`belongs_to`, `has_many`, `has_one`, `has_and_belongs_to_many`)
- Enums
- Simple scopes (one-liner queries)
- Delegations

**FORBIDDEN in models:**
- `validates` (use contracts)
- Callbacks (except `before_destroy` for attachment cleanup)
- Complex queries (use filters)
- Business logic (use services)

---

## Background Jobs (Full Example)

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

**Solid Queue:**
```ruby
class ProcessJob < ApplicationJob
  queue_as :default

  def perform(feature_id)
    Feature.find(feature_id).then { ProcessService.new(feature: _1).call }
  rescue ActiveRecord::RecordNotFound => e
    Rails.logger.error("Feature ##{feature_id} not found")
  end
end
```

**Key principles:**
- Jobs are idempotent (can run multiple times safely)
- Accept IDs, not AR objects
- Handle `RecordNotFound` gracefully
- Delegate to services for business logic
- Configure retry strategy

---

## Hotwire Patterns

**Turbo Frames:**
```erb
<%= turbo_frame_tag "list" do %>
  <% @items.each { |i| render i } %>
<% end %>

<%= link_to "Filter", path, data: { turbo_frame: "list" } %>
```

**Turbo Streams:**

Available actions: `append`, `prepend`, `replace`, `update`, `remove`

```erb
<!-- app/views/features/create.turbo_stream.erb -->
<%= turbo_stream.append "features" do %>
  <%= render @feature %>
<% end %>
```

**Stimulus Controller:**
```javascript
// app/javascript/controllers/clipboard_controller.js
import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["source"]

  copy() {
    navigator.clipboard.writeText(this.sourceTarget.value)
  }
}
```

```erb
<div data-controller="clipboard">
  <input data-clipboard-target="source" value="Copy me!">
  <button data-action="click->clipboard#copy">Copy</button>
</div>
```

---

## Testing Patterns

**Factory (FactoryBot):**
```ruby
factory :feature do
  user
  sequence(:name) { "Feature #{_1}" }
  trait(:published) { status { :published } }
end

# Performance: build_stubbed > build > create
let(:user) { build_stubbed(:user) }
```

**Service Test:**
```ruby
describe '#call' do
  it 'creates feature' do
    expect { service.call }.to change(Feature, :count).by(1)
  end

  it 'schedules job' do
    expect { service.call }.to have_enqueued_job(ProcessJob)
  end
end
```

**Form Test:**
```ruby
describe '#save' do
  context 'with valid params' do
    it 'returns true' do
      expect(form.save).to be true
    end

    it 'creates feature' do
      expect { form.save }.to change(Feature, :count).by(1)
    end
  end

  context 'with invalid params' do
    let(:params) { { name: '' } }

    it 'returns false' do
      expect(form.save).to be false
    end

    it 'populates errors' do
      form.save
      expect(form.errors[:name]).to include('must be filled')
    end
  end
end
```

**Controller Test (RSpec + Request specs):**
```ruby
describe 'POST /features' do
  context 'with valid params' do
    it 'creates feature' do
      expect { post features_path, params: { name: 'Test' } }.to change(Feature, :count).by(1)
    end

    it 'returns 201' do
      post features_path, params: { name: 'Test' }
      expect(response).to have_http_status(:created)
    end
  end

  context 'with invalid params' do
    it 'returns 422' do
      post features_path, params: { name: '' }
      expect(response).to have_http_status(:unprocessable_entity)
    end
  end
end
```

---

## Filter Pattern

```ruby
class FeaturesFilter
  def self.result(params, scope)
    new(params, scope).result
  end

  def initialize(params, scope)
    @params = params
    @scope = scope
  end

  def result
    filter_by_status
    filter_by_search
    @scope
  end

  private

  def filter_by_status
    return unless @params[:status].present?
    @scope = @scope.where(status: @params[:status])
  end

  def filter_by_search
    return unless @params[:q].present?
    @scope = @scope.where('name ILIKE ?', "%#{@params[:q]}%")
  end
end
```

**Key principles:**
- Class method `.result` for convenience
- Instance methods for chainable filters
- Return scope, not collection
- Each filter checks params presence
