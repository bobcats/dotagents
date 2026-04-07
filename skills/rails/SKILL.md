---
name: rails
description: "Idiomatic Rails patterns, anti-patterns, and code quality detection. Use when working in a Rails application — writing, reviewing, or refactoring."
metadata:
  category: languages
---

# Rails

Apply these patterns when writing, reviewing, or refactoring Rails code. Load the `ruby` skill alongside this one.

## Detection Patterns

```bash
rg "scope :\w+" --type ruby  # check if scopes are used
rg "before_action|after_action" --type ruby  # check if callbacks needed
rg "helper_method :" --type ruby  # check if helpers used in views
```

### Performance

```bash
# Eager loading usage
rg "includes\(|preload\(|eager_load\(" --type ruby
rg "strict_loading" --type ruby  # Rails 6.1+ N+1 prevention

# Query patterns
rg "\.where\(.*\)\.where\(" --type ruby  # chainable → single where
rg "\.pluck\(" --type ruby  # vs select for large sets
rg "find_each|in_batches" --type ruby  # batch processing

# Potential N+1 indicators
rg "\.each.*\n.*\.(find|where|count)" --multiline --type ruby
rg "\.all\b" --type ruby  # unbounded queries

# Async queries (Rails 7+)
rg "load_async|async_count|async_sum" --type ruby
```

### Anti-Patterns

```bash
# Callback abuse
rg "after_save|after_commit|before_save" --type ruby  # review for side effects
rg "after_save.*enqueue|after_commit.*perform" --type ruby  # job queuing in callbacks

# default_scope (avoid entirely)
rg "default_scope" --type ruby

# Fat models/controllers
rg "class \w+Controller" --type ruby -A 50 | head -100  # review action sizes
```

## Idiomatic Rails

### Eager Loading Strategy

```ruby
# preload: Separate queries, can't filter by association
User.preload(:posts)  # 2 queries: users, then posts

# eager_load: LEFT OUTER JOIN, use when filtering/sorting by association
User.eager_load(:posts).where(posts: { published: true })
User.eager_load(:posts).order("posts.created_at DESC")

# includes: Rails chooses (preload unless conditions on association)
User.includes(:posts)  # preload by default
User.includes(:posts).where(posts: { published: true })  # eager_load

# strict_loading: Raises error if lazy load attempted (Rails 6.1+)
user = User.strict_loading.first
user.posts  # raises ActiveRecord::StrictLoadingViolationError
```

### Query Optimization

```ruby
# find_each for large datasets
User.all.each { |u| process(u) }  # loads all into memory →
User.find_each { |u| process(u) }

# pluck for values (faster, returns array)
User.all.map(&:email)  # instantiates AR objects →
User.pluck(:email)

# select for AR objects with subset of columns
User.select(:id, :email).find_each { |u| ... }

# exists? over present? (doesn't load records)
User.where(email: email).present?  # loads records →
User.exists?(email: email)

# counter_cache for counts
belongs_to :author, counter_cache: true
# Then: author.posts_count instead of author.posts.count

# update_all for bulk updates
users.each { |u| u.update(active: false) }  # N queries →
users.update_all(active: false)
```

### Async Queries (Rails 7+)

```ruby
# Parallel query execution for slow queries
# Requires: config.active_record.async_query_executor = :global_thread_pool

posts = Post.where(published: true).load_async
users = User.where(active: true).load_async
# Both queries run in parallel, block when accessed

# Async aggregates (Rails 7.1+)
count_promise = Post.async_count
sum_promise = Order.async_sum(:total)
# Access with count_promise.value
```

### Avoid default_scope

```ruby
# default_scope causes surprises:
class Post < ApplicationRecord
  default_scope { where(deleted: false) }  # DON'T
end

Post.all  # silently excludes deleted
Post.new  # sets deleted: false implicitly
Post.deleted  # returns NOTHING if scope conflicts

# Use explicit scopes instead:
class Post < ApplicationRecord
  scope :active, -> { where(deleted: false) }
  scope :deleted, -> { where(deleted: true) }
end

Post.all     # all posts
Post.active  # non-deleted
Post.deleted # deleted
```

### Avoid Callback Side Effects

```ruby
# Callbacks for side effects cause problems:
class Order < ApplicationRecord
  after_save :send_confirmation_email  # DON'T
  after_commit :enqueue_fulfillment    # Race condition risk
end

# Problems:
# - after_save: record not visible to other connections yet
# - No context about why the save happened
# - Hard to test, hard to skip

# Use service objects instead:
module Orders
  module_function

  def place(order)
    order.save!
    OrderMailer.confirmation(order).deliver_later
    FulfillmentJob.perform_later(order.id)
  end
end

# Callbacks OK for: data normalization, computed caches
class User < ApplicationRecord
  before_validation :normalize_email

  private

  def normalize_email
    self.email = email&.downcase&.strip
  end
end
```

### Scopes Over Class Methods

```ruby
# Class methods don't chain as cleanly:
def self.published
  where(published: true)
end
def self.recent
  order(created_at: :desc)
end  # →

# Scopes are chainable and intention-revealing:
scope :published, -> { where(published: true) }
scope :recent, -> { order(created_at: :desc) }

Post.published.recent  # clear chain
```

### Query Objects for Complex Queries

```ruby
# Complex query in controller:
@users = User.joins(:orders)
             .where(orders: { created_at: 30.days.ago.. })
             .group(:id)
             .having("COUNT(orders.id) > 5")
             .order("COUNT(orders.id) DESC")  # →

# Extract to query object:
class FrequentBuyers
  def initialize(relation = User.all)
    @relation = relation
  end

  def call(min_orders: 5, period: 30.days)
    @relation
      .joins(:orders)
      .where(orders: { created_at: period.ago.. })
      .group(:id)
      .having("COUNT(orders.id) > ?", min_orders)
      .order("COUNT(orders.id) DESC")
  end
end

@users = FrequentBuyers.new.call
```

### Background Jobs

```ruby
# Structure every job the same way:
class ProcessOrderJob < ApplicationJob
  def perform(order_id)
    # 1. Idempotency guard - already processed?
    order = Order.find(order_id)
    return if order.processed?

    # 2. Precondition guard - valid state?
    return unless order.paid?

    # 3. Do the work
    Orders.process(order)
  end
end

# Rescue specific exceptions, never bare rescue
class ExternalApiJob < ApplicationJob
  retry_on Net::TimeoutError, Errno::ECONNREFUSED, wait: :polynomially_longer
  discard_on ActiveRecord::RecordNotFound  # Fatal, don't retry

  def perform(record_id)
    # ...
  end
end

# Single hash for arguments (deploy safety)
# BAD: positional args break if you add/remove params mid-deploy
ProcessOrderJob.perform_later(order_id, notify: true)

# GOOD: hash is forward/backward compatible
ProcessOrderJob.perform_later(order_id: order_id, notify: true)
```

### Migrations

Always use `rails g migration` to create migration files — never hand-create them. Hand-created files risk wrong timestamps, missing version numbers, or incorrect class naming.

Use `db:rollback` (not `db:reset`) when iterating on a migration in development. `db:reset` drops and recreates the entire database, losing all data and running all migrations from scratch.

```ruby
# Always use explicit up/down (never `change`)
class AddStatusToOrders < ActiveRecord::Migration[7.1]
  def up
    add_column :orders, :status, :string, default: "pending"
    add_index :orders, :status, algorithm: :concurrently
  end

  def down
    remove_column :orders, :status
  end
end

# Verify migrations are redoable:
# RAILS_ENV=test rails db:migrate:redo
```

#### pg_ha_migrations

If the project uses `pg_ha_migrations` (check `rg "pg_ha_migrations" Gemfile`):

**One operation per migration.** pg_ha_migrations disables DDL transactions, so if migration fails midway, you're left in a bad state.

```ruby
# 20240101_add_status_to_orders.rb
class AddStatusToOrders < ActiveRecord::Migration[7.1]
  def up
    safe_add_column :orders, :status, :string, default: "pending"
  end

  def down
    unsafe_remove_column :orders, :status
  end
end

# 20240102_add_index_on_orders_status.rb (separate migration)
class AddIndexOnOrdersStatus < ActiveRecord::Migration[7.1]
  def up
    safe_add_concurrent_index :orders, :status
  end

  def down
    remove_index :orders, :status
  end
end
```

### Optional Foreign Keys

Adding `optional: true` to an association has large blast radius:
- Views may render nil
- Serializers need null handling
- API responses change shape
- Audit trails lose context

Investigate all consumers before making an FK optional.
