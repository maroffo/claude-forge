---
name: rails
description: "Ruby on Rails with service-oriented architecture, Dry-validation, Sidekiq. Use for Rails API, Rails services, Rails forms, RSpec, ActiveRecord, Rails migrations."
allowed-tools: [mcp__acp__Read, mcp__acp__Edit, mcp__acp__Write, mcp__acp__Bash]
---

# ABOUTME: Rails service-oriented architecture, validation contracts, background jobs
# ABOUTME: API development with thin controllers, services, forms, filters, and Sidekiq

# Ruby on Rails - Service-Oriented Architecture

## Quick Reference

```bash
# Quality checks
bundle exec lefthook run all

# Run tests
bundle exec rspec

# Run server
rails s

# Generate
rails g migration CreateUsers
rails g model User
rails g controller Api::V1::Users

# Database
rails db:migrate
rails db:rollback
rails db:seed

# Console
rails c
```

**Architecture patterns:**
```ruby
# Service
MyService.new(user: user, params: params).call

# Form
MyForm.new(params, user).save

# Filter
MyFilter.result(params, scope)

# Job
MyJob.perform_async(record_id)
```

**Navigation:**
- [§ Sacred Rules](#sacred-rules)
- [§ Service Pattern](#-service-pattern)
- [§ Form & Contract Pattern](#-form--contract-pattern)
- [§ Filter Pattern](#-filter-pattern)
- [§ Controller Pattern](#-controller-pattern)
- [§ Model Pattern](#-model-pattern)
- [§ Background Jobs](#-background-jobs)
- [§ Database Patterns](#-database-patterns)
- [§ Testing](#-testing)

**See also:**
- Code search: `_AST_GREP.md`
- Patterns: `_PATTERNS.md`
- Git: `source-control`

---

## Sacred Rules

These are **NON-NEGOTIABLE** principles:

### The Sacred Rules

1. **NO LOGIC IN CONTROLLERS** - Controllers are thin, only handle HTTP layer
2. **ALL LOGIC IN SERVICES, FORMS, AND FILTERS** - Business logic must be isolated
3. **NO ACTIVE RECORD VALIDATIONS** - Validation only via contracts (Dry-validation)
4. **MINIMUM LOGIC IN MODELS** - Models are data structures with associations
5. **NO MODEL CALLBACKS** - Only exception: Attachment destruction from storage

---

## § Service Pattern

**All business logic MUST be in services.**

**Service Characteristics:**
- Single responsibility
- Takes validated input
- Performs business operations
- Returns result or raises exceptions
- Can call other services
- Testable in isolation

**Service Template:**

```ruby
# app/services/feature/operation_service.rb
module Feature
  class OperationService
    attr_reader :user, :params

    def initialize(user:, params:)
      @user = user
      @params = params
    end

    def call
      validate_preconditions
      perform_operation
      trigger_side_effects
      result
    end

    private

    def validate_preconditions
      raise UnauthorizedError unless user.can_perform_operation?
    end

    def perform_operation
      ActiveRecord::Base.transaction do
        @record = create_record
        update_related_records
      end
    end

    def trigger_side_effects
      # Schedule background jobs
      Feature::ProcessJob.perform_async(@record.id)
      
      # Track analytics
      Analytics::TrackJob.perform_async(user.id, 'operation_performed')
    end

    def result
      OpenStruct.new(
        success: true,
        record: @record,
        message: 'Operation completed successfully'
      )
    end

    def create_record
      user.feature_records.create!(
        name: params[:name],
        status: :pending
      )
    end

    def update_related_records
      user.update!(last_operation_at: Time.current)
    end
  end
end
```

**Service Usage:**
```ruby
result = Feature::OperationService.new(
  user: current_user,
  params: validated_params
).call

if result.success
  render json: result.record, status: :created
else
  render json: { error: result.message }, status: :unprocessable_entity
end
```

**Key Points:**
- Services use `#call` as main entry point
- Return OpenStruct for structured results
- Use transactions for multi-step operations
- Schedule jobs AFTER successful persistence
- Clear separation of concerns

---

## § Form & Contract Pattern

### 2.1 Two-Part Validation System

**Contracts** - Define validation rules (Dry-validation)
**Forms** - Orchestrate validation + persistence

### 2.2 Contract Pattern

```ruby
# app/contracts/api/v1/features/create_contract.rb
module Api
  module V1
    module Features
      class CreateContract < Dry::Validation::Contract
        params do
          required(:name).filled(:string, max_size?: 255)
          required(:description).filled(:string)
          optional(:category_id).filled(:integer)
          optional(:tags).array(:string)
        end

        rule(:name) do
          if Feature.exists?(name: value.downcase)
            key.failure(I18n.t('errors.messages.taken'))
          end
        end

        rule(:category_id) do
          unless Category.exists?(id: value)
            key.failure('must exist')
          end
        end
      end
    end
  end
end
```

**Contract Features:**
- `params` - Schema definition
- `required`/`optional` - Field presence
- `:filled` - Must not be blank
- Type checking (`:string`, `:integer`, `:array`)
- Size validation (`max_size?`, `min_size?`)
- Format validation (`format?`)
- Custom rules with `rule(:field_name)`

### 2.3 Form Pattern (BaseForm)

```ruby
# app/forms/base_form.rb
class BaseForm
  attr_reader :errors, :model, :models

  def initialize(attributes)
    @attributes = attributes
    @errors = {}
  end

  def valid?
    result = @contract.call(@attributes)
    @errors = result.errors.to_h
    result.success?
  end

  def save
    return false unless valid?
    persist!
    true
  rescue => e
    @errors[:base] = [e.message]
    false
  end

  def error_messages
    @errors.map { |key, messages| "#{key}: #{messages.join(', ')}" }.join('; ')
  end

  private

  def validated_params
    @contract.call(@attributes).to_h
  end

  def persist!
    raise NotImplementedError, 'Subclasses must implement #persist!'
  end
end
```

**Form Implementation:**

```ruby
# app/forms/api/v1/features/create_form.rb
module Api
  module V1
    module Features
      class CreateForm < BaseForm
        def initialize(attributes, current_user)
          super(attributes)
          @current_user = current_user
          @contract = Api::V1::Features::CreateContract.new
        end

        private

        def persist!
          ActiveRecord::Base.transaction do
            @model = Feature.create!(
              name: validated_params[:name],
              description: validated_params[:description],
              category_id: validated_params[:category_id],
              user: @current_user,
              status: :draft
            )

            create_tags if validated_params[:tags].present?
          end

          schedule_jobs
        end

        def create_tags
          validated_params[:tags].each do |tag_name|
            @model.tags.create!(name: tag_name)
          end
        end

        def schedule_jobs
          Features::ProcessJob.perform_async(@model.id)
          Analytics::TrackJob.perform_async(@current_user.id, 'feature_created')
        end
      end
    end
  end
end
```

**Controller Usage:**
```ruby
form = Api::V1::Features::CreateForm.new(params, current_user)

if form.save
  render json: form.model, status: :created
else
  render json: { errors: form.errors }, status: :unprocessable_entity
end
```

**Key Points:**
- Forms inherit from `BaseForm`
- `@contract` must be set in `initialize`
- Override `persist!` for save logic
- Use `validated_params` to access validated data
- `@model` or `@models` for return values
- Schedule jobs AFTER transaction

---

## § Filter Pattern

### 3.1 BaseFilter

**Filters handle list queries with complex logic.**

```ruby
# app/filters/base_filter.rb
class BaseFilter
  attr_reader :params

  def initialize(params, scope = nil)
    @params = params || {}
    @scope = scope
  end

  def result
    raise NotImplementedError
  end

  def self.result(*args)
    new(*args).result
  end

  protected

  def chain_queries(relation, *methods)
    methods.reduce(relation) do |rel, method|
      send(method, rel)
    end
  end

  def none_relation
    @scope.none
  end

  def self.define_params_fields_getters(fields)
    fields.each do |field|
      define_method(field) { params[field] }
    end
  end
end
```

### 3.2 Filter Implementation

```ruby
# app/filters/api/v1/features_filter.rb
module Api
  module V1
    class FeaturesFilter < BaseFilter
      ALLOWED_STATUSES = %w[draft published archived].freeze
      ALLOWED_SORT_BY = %w[created_at updated_at name].freeze
      
      FIELDS = %i[status category_id user_id sort_by order].freeze
      define_params_fields_getters(FIELDS)

      def initialize(params, scope = Feature)
        @params = params || {}
        @scope = scope
      end

      def result
        @result ||= chain_queries(
          relation,
          :filter_by_status,
          :filter_by_category,
          :filter_by_user,
          :apply_ordering
        )
      end

      private

      def relation
        @scope.all
      end

      def filter_by_status(relation)
        return relation unless status.present?
        return relation unless ALLOWED_STATUSES.include?(status)
        
        relation.where(status: status)
      end

      def filter_by_category(relation)
        return relation unless category_id.present?
        relation.where(category_id: category_id)
      end

      def filter_by_user(relation)
        return relation unless user_id.present?
        relation.where(user_id: user_id)
      end

      def apply_ordering(relation)
        sort_field = ALLOWED_SORT_BY.include?(sort_by) ? sort_by : 'created_at'
        sort_order = order == 'asc' ? :asc : :desc
        
        relation.order(sort_field => sort_order)
      end
    end
  end
end
```

**Controller Usage:**
```ruby
features = Api::V1::FeaturesFilter.result(
  filter_params,
  current_user.features
).includes(:category, :tags)

render json: features
```

**Key Points:**
- Filters use method chaining
- Each method takes and returns `ActiveRecord::Relation`
- Use `none_relation` for empty results
- Whitelist allowed filter values
- Can integrate with pagination gems

---

## § Controller Pattern

### 4.1 Thin Controllers

**Controllers ONLY handle HTTP layer.**

```ruby
# app/controllers/api/v1/features_controller.rb
module Api
  module V1
    class FeaturesController < Api::V1::BaseController
      before_action :authenticate_user!
      before_action :set_feature, only: [:show, :update, :destroy]

      def index
        features = Api::V1::FeaturesFilter.result(
          filter_params,
          current_user.features
        )
        
        render json: features
      end

      def show
        render json: @feature
      end

      def create
        form = Api::V1::Features::CreateForm.new(
          feature_params,
          current_user
        )

        if form.save
          render json: form.model, status: :created
        else
          render json: { errors: form.errors }, status: :unprocessable_entity
        end
      end

      def update
        form = Api::V1::Features::UpdateForm.new(
          feature_params,
          @feature
        )

        if form.save
          render json: form.model
        else
          render json: { errors: form.errors }, status: :unprocessable_entity
        end
      end

      def destroy
        @feature.destroy
        head :no_content
      end

      private

      def set_feature
        @feature = current_user.features.find(params[:id])
      end

      def feature_params
        params.require(:feature).permit(:name, :description, :category_id, tags: [])
      end

      def filter_params
        params.permit(:status, :category_id, :sort_by, :order)
      end
    end
  end
end
```

**Controller Rules:**
- NO business logic
- Use forms for creation/updates
- Use filters for queries
- Use services for complex operations
- Handle only HTTP concerns

---

## § Model Pattern

### 5.1 Minimal Models

**Models are data structures with associations.**

```ruby
# app/models/feature.rb
class Feature < ApplicationRecord
  acts_as_paranoid  # Soft deletes

  # Associations
  belongs_to :user
  belongs_to :category
  has_many :tags, dependent: :destroy
  has_many :comments, as: :commentable, dependent: :destroy

  # Enums
  enum status: { draft: 0, published: 1, archived: 2 }

  # Scopes
  scope :recent, -> { order(created_at: :desc) }
  scope :active, -> { where(status: [:draft, :published]) }
  scope :by_category, ->(category_id) { where(category_id: category_id) }

  # Class methods
  def self.search(query)
    where('name ILIKE ? OR description ILIKE ?', "%#{query}%", "%#{query}%")
  end

  # Instance methods (minimal)
  def published?
    status == 'published'
  end

  def can_be_edited_by?(user)
    self.user == user
  end
end
```

**Model Rules:**
- Associations and relationships
- Enums for status fields
- Simple scopes
- Minimal instance methods
- NO validation (use contracts)
- NO callbacks (except attachment cleanup)
- NO business logic

---

## § Background Jobs (Sidekiq)

### 6.1 Job Pattern

```ruby
# app/jobs/features/process_job.rb
module Features
  class ProcessJob
    include Sidekiq::Job
    
    sidekiq_options retry: 3

    def perform(feature_id)
      Rails.logger.tagged('Features::ProcessJob').info(
        "Processing feature ##{feature_id}"
      )
      
      feature = Feature.find(feature_id)
      Features::ProcessService.new(feature: feature).call
      
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.error("Feature ##{feature_id} not found: #{e.message}")
    end
  end
end
```

**Job with Throttling:**
```ruby
module Features
  class ProcessJob
    include Sidekiq::Job
    include Sidekiq::Throttled::Job

    sidekiq_throttle(
      concurrency: { limit: 1, key_suffix: ->(feature_id) { feature_id } }
    )

    def perform(feature_id)
      # Process feature
    end
  end
end
```

**Scheduling Jobs:**
```ruby
# Async (enqueue for later)
Features::ProcessJob.perform_async(feature.id)

# Delayed (enqueue with delay)
Features::ProcessJob.perform_in(5.minutes, feature.id)

# Scheduled (specific time)
Features::ProcessJob.perform_at(1.hour.from_now, feature.id)
```

**Job Rules:**
- Idempotent (safe to retry)
- Pass IDs, not objects
- Handle missing records gracefully
- Log important events
- Use appropriate retry strategies
- Keep jobs focused and fast

---

## § Database Patterns

### 7.1 Migrations

```ruby
# db/migrate/20250104_create_features.rb
class CreateFeatures < ActiveRecord::Migration[7.0]
  def change
    create_table :features, id: :uuid do |t|
      t.string :name, null: false
      t.text :description
      t.integer :status, default: 0, null: false
      t.references :user, null: false, foreign_key: true, type: :uuid
      t.references :category, null: true, foreign_key: true, type: :uuid
      
      t.timestamps
      t.datetime :deleted_at
    end

    add_index :features, :name
    add_index :features, :status
    add_index :features, :deleted_at
  end
end
```

### 7.2 Database Views (Scenic)

**Generate View:**
```bash
rails generate scenic:view features_with_stats
```

**View SQL:**
```sql
-- db/views/features_with_stats_v01.sql
SELECT
  features.id,
  features.name,
  features.status,
  COUNT(DISTINCT comments.id) AS comments_count,
  COUNT(DISTINCT tags.id) AS tags_count,
  features.created_at
FROM features
LEFT JOIN comments ON features.id = comments.commentable_id
  AND comments.commentable_type = 'Feature'
LEFT JOIN tags ON features.id = tags.feature_id
WHERE features.deleted_at IS NULL
GROUP BY features.id;
```

**Migration:**
```ruby
class CreateFeaturesWithStats < ActiveRecord::Migration[7.0]
  def change
    create_view :features_with_stats
  end
end
```

**Model:**
```ruby
class FeaturesWithStats < ApplicationRecord
  self.primary_key = 'id'
  
  # Read-only view
  def readonly?
    true
  end
end
```

**Usage:**
```ruby
FeaturesWithStats.where(status: :published).limit(10)
```

---

## § Testing with RSpec

### 8.1 Service Spec

```ruby
# spec/services/features/create_service_spec.rb
require 'rails_helper'

RSpec.describe Features::CreateService do
  let(:user) { create(:user) }
  let(:params) do
    {
      name: 'Test Feature',
      description: 'Test description'
    }
  end
  
  subject(:service) { described_class.new(user: user, params: params) }

  describe '#call' do
    context 'with valid params' do
      it 'creates a feature' do
        expect { service.call }.to change(Feature, :count).by(1)
      end

      it 'returns success result' do
        result = service.call
        expect(result.success).to be true
        expect(result.record).to be_a(Feature)
      end

      it 'schedules background job' do
        expect(Features::ProcessJob).to receive(:perform_async)
        service.call
      end
    end

    context 'with invalid params' do
      let(:params) { { name: '' } }

      it 'raises validation error' do
        expect { service.call }.to raise_error(ActiveRecord::RecordInvalid)
      end
    end
  end
end
```

### 8.2 Form Spec

```ruby
# spec/forms/api/v1/features/create_form_spec.rb
require 'rails_helper'

RSpec.describe Api::V1::Features::CreateForm do
  let(:user) { create(:user) }
  let(:params) do
    {
      name: 'Test Feature',
      description: 'Test description'
    }
  end

  subject(:form) { described_class.new(params, user) }

  describe '#valid?' do
    context 'with valid params' do
      it 'returns true' do
        expect(form.valid?).to be true
      end
    end

    context 'with missing name' do
      let(:params) { { description: 'Test' } }

      it 'returns false' do
        expect(form.valid?).to be false
        expect(form.errors[:name]).to be_present
      end
    end
  end

  describe '#save' do
    it 'creates feature' do
      expect { form.save }.to change(Feature, :count).by(1)
    end

    it 'returns true' do
      expect(form.save).to be true
    end

    it 'sets model' do
      form.save
      expect(form.model).to be_a(Feature)
    end
  end
end
```

### 8.3 Request Spec (API)

```ruby
# spec/requests/api/v1/features_spec.rb
require 'rails_helper'

RSpec.describe 'Api::V1::Features', type: :request do
  let(:user) { create(:user) }
  let(:headers) { { 'Authorization' => "Bearer #{user.token}" } }

  describe 'POST /api/v1/features' do
    let(:params) do
      {
        feature: {
          name: 'Test Feature',
          description: 'Test description'
        }
      }
    end

    context 'with valid params' do
      it 'creates feature' do
        expect do
          post '/api/v1/features', params: params, headers: headers
        end.to change(Feature, :count).by(1)
      end

      it 'returns created status' do
        post '/api/v1/features', params: params, headers: headers
        expect(response).to have_http_status(:created)
      end

      it 'returns feature data' do
        post '/api/v1/features', params: params, headers: headers
        json = JSON.parse(response.body)
        expect(json['name']).to eq('Test Feature')
      end
    end

    context 'with invalid params' do
      let(:params) { { feature: { name: '' } } }

      it 'returns unprocessable entity' do
        post '/api/v1/features', params: params, headers: headers
        expect(response).to have_http_status(:unprocessable_entity)
      end

      it 'returns errors' do
        post '/api/v1/features', params: params, headers: headers
        json = JSON.parse(response.body)
        expect(json['errors']).to be_present
      end
    end
  end
end
```

---

## § Code Quality

### 9.1 Pre-commit Checks

**ALWAYS run before MR:**
```bash
bundle exec lefthook run all
```

This runs:
- Rubocop (style)
- Brakeman (security)
- Bundle Audit (vulnerabilities)
- RSpec (tests)

### 9.2 Rubocop Configuration

```yaml
# .rubocop.yml
inherit_from: .rubocop_todo.yml

AllCops:
  NewCops: enable
  TargetRubyVersion: 3.4
  Exclude:
    - 'bin/**/*'
    - 'db/**/*'
    - 'config/**/*'
    - 'vendor/**/*'

Layout/LineLength:
  Max: 120

Metrics/MethodLength:
  Max: 20

Metrics/ClassLength:
  Max: 200
```

---

## § Common Patterns

### 10.1 API Endpoint Implementation

**Step-by-step:**

1. **Create Contract** (validation)
2. **Create Form** (validation + persistence)
3. **Create Service** (business logic)
4. **Create Controller Action** (HTTP handling)
5. **Add Route**
6. **Write Tests**

### 10.2 Background Job Implementation

1. **Create Job Class**
2. **Implement `perform` method**
3. **Add error handling**
4. **Schedule from service/form**
5. **Write Tests**

### 10.3 Database View Implementation

1. **Generate with Scenic**
2. **Write SQL**
3. **Create Model**
4. **Write Migration**
5. **Query in code**

---

## § Architecture Checklist

Before every commit:
- [ ] NO logic in controllers
- [ ] ALL validation in contracts
- [ ] Business logic in services
- [ ] Minimal model logic
- [ ] NO model callbacks (except attachments)
- [ ] Background jobs idempotent
- [ ] Tests cover functionality
- [ ] Rubocop passes
- [ ] Brakeman passes
- [ ] All tests pass

---

## § Resources

**Official:**
- https://guides.rubyonrails.org/
- https://dry-rb.org/gems/dry-validation/
- https://github.com/mperham/sidekiq/wiki

**Gems:**
- Dry-validation (contracts)
- Sidekiq (background jobs)
- Scenic (database views)
- Pundit (authorization)
- Panko (serialization)

---

**End of SKILL: Ruby on Rails**
