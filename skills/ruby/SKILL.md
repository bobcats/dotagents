---
name: ruby
description: "Idiomatic Ruby patterns, anti-patterns, and code quality detection. Use when writing, reviewing, or refactoring Ruby code."
metadata:
  category: languages
---

# Ruby

Apply these patterns when writing, reviewing, or refactoring Ruby code.

## Detection Patterns

Use these to find issues in existing code.

### Dead Code

```bash
# Method definitions (compare against calls to find unused)
rg "def (self\.)?\w+" --type ruby -o | sort | uniq

# Commented-out code blocks (3+ consecutive lines)
rg "^(\s*)#[^!].*\n\1#.*\n\1#" --multiline --type ruby

# Unused method parameters (underscore prefix convention)
rg "def \w+\(.*_\w+" --type ruby

# Class variables (often a smell, rarely needed)
rg "@@\w+" --type ruby
```

### Types

```bash
# Repeated hash shapes → extract to Data or Struct
rg "\{ \w+: .*, \w+: .*\}" --type ruby

# Long parameter lists (4+) → extract to Data/Struct
rg "def \w+\([^)]*,[^)]*,[^)]*," --type ruby

# Boolean parameters (boolean blindness)
rg "def \w+\([^)]*: (true|false|Boolean)" --type ruby
rg "\w+\((true|false)(,|\))" --type ruby  # boolean literals at call sites
```

### Tests

```bash
# Skipped/pending tests
rg "(skip|pending)" --glob "*_spec.rb" --glob "*_test.rb"

# Assertion density (low count = suspicious)
rg "(expect|assert)" --type ruby -c | sort -t: -k2 -n
```

### Complexity

```bash
# Deep nesting (4+ levels / 8+ spaces)
rg "^\s{8,}(if|unless|case|while|until)" --type ruby

# Long method chains (possible feature envy)
rg "\.\w+.*\.\w+.*\.\w+.*\.\w+" --type ruby

# Nested iterators
rg "\.each.*do.*\n.*\.each.*do" --multiline --type ruby
```

### Performance

```bash
# N+1 queries (find/where inside loop)
rg "\.each.*do.*\n.*\.(find|where)" --multiline --type ruby

# Unbounded queries
rg "\.all\b" --type ruby

# Chained enumerables that could combine
rg "\.map.*\.map|\.select.*\.select|\.map.*\.flatten" --type ruby
```

## Idiomatic Ruby

### Data Over Objects

```ruby
# Use Data.define for immutable value objects (Ruby 3.2+)
class Point
  attr_reader :x, :y
  def initialize(x, y)
    @x, @y = x, y
  end
end  # →

Point = Data.define(:x, :y)

# For older Ruby, use Struct with freeze
Point = Struct.new(:x, :y) do
  def initialize(...)
    super
    freeze
  end
end

# Data objects support pattern matching
case point
in Point(x: 0, y:) then "on y-axis at #{y}"
in Point(x:, y: 0) then "on x-axis at #{x}"
end

# Use with() for immutable updates
point = Point.new(1, 2)
moved = point.with(x: 10)  # => Point(x: 10, y: 2)
```

### Module Functions Over Stateful Classes

```ruby
# Instead of stateful service objects:
class UserValidator
  def initialize(user)
    @user = user
  end
  def validate
    # ...
  end
end
UserValidator.new(user).validate  # →

# Use module functions:
module Users
  module_function

  def validate(user)
    # pure function, no state
  end
end
Users.validate(user)
```

### Guard Clauses

```ruby
# Deeply nested conditionals:
def process(order)
  if order.valid?
    if order.paid?
      if order.in_stock?
        ship(order)
      end
    end
  end
end  # →

# Guard clauses - flat and readable:
def process(order)
  return unless order.valid?
  return unless order.paid?
  return unless order.in_stock?

  ship(order)
end
```

### Nil Handling

```ruby
# Hash#fetch over Hash#[] to avoid nil propagation
config[:timeout]  # returns nil if missing →
config.fetch(:timeout)  # raises KeyError
config.fetch(:timeout, 30)  # default value
config.fetch(:timeout) { calculate_default }  # lazy default

# Safe navigation for optional chains
user && user.profile && user.profile.avatar  # →
user&.profile&.avatar

# dig for nested hash access
hash[:a] && hash[:a][:b] && hash[:a][:b][:c]  # →
hash.dig(:a, :b, :c)
```

### Enumerable Patterns

```ruby
# Prefer enumerable methods over loops
result = []
items.each { |x| result << x.name if x.active? }  # →
result = items.select(&:active?).map(&:name)

# Symbol to proc for simple accessors
items.map { |x| x.name }  # →
items.map(&:name)

# flat_map over map + flatten
items.map { |x| x.tags }.flatten  # →
items.flat_map(&:tags)

# each_with_object for building collections
items.reduce({}) { |h, x| h[x.id] = x; h }  # →
items.each_with_object({}) { |x, h| h[x.id] = x }

# transform_keys/transform_values for hashes
hash.map { |k, v| [k.to_s, v * 2] }.to_h  # →
hash.transform_keys(&:to_s).transform_values { |v| v * 2 }
```

### Pattern Matching (Ruby 3+)

```ruby
# Case/when with pattern matching
case response
when { status: 200, body: body }
  handle_success(body)
when { status: 404 }
  handle_not_found
when { status: 500, error: error }
  handle_error(error)
end

# In expressions for assertions
response => { status:, body: }
# raises NoMatchingPatternError if structure doesn't match
```

### Boolean Blindness

```ruby
# Boolean parameters hide intent at call sites:
def send_email(user, urgent)
  # ...
end
send_email(user, true)  # what does true mean? →

# Use symbols or constants:
def send_email(user, priority: :normal)
  # ...
end
send_email(user, priority: :urgent)

# Or define an enum-like module:
module Priority
  NORMAL = :normal
  URGENT = :urgent
end
send_email(user, priority: Priority::URGENT)
```

### Parse, Don't Validate

```ruby
# Validating then using raw data:
def process(params)
  raise ArgumentError unless params[:email].match?(EMAIL_REGEX)
  raise ArgumentError unless params[:age].is_a?(Integer)
  # now use params[:email], params[:age] everywhere... →

# Parse into typed structure at boundary:
User = Data.define(:email, :age) do
  def self.parse(params)
    email = params.fetch(:email)
    age = params.fetch(:age)
    raise ArgumentError, "invalid email" unless email.match?(EMAIL_REGEX)
    raise ArgumentError, "invalid age" unless age.is_a?(Integer) && age > 0
    new(email:, age:)
  end
end

def process(params)
  user = User.parse(params)  # invalid states now impossible
  # user.email and user.age are guaranteed valid
end
```

### Immutability

```ruby
# Prefer Data.define (immutable) over Struct:
Point = Data.define(:x, :y)
point = Point.new(x: 1, y: 2)
point.x = 10  # raises FrozenError

# Use with() for updates (returns new instance):
moved = point.with(x: 10)  # point unchanged

# Freeze mutable objects at creation:
CONFIG = { timeout: 30, retries: 3 }.freeze
```
