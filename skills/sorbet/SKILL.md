---
name: sorbet
description: "Idiomatic Sorbet patterns, anti-patterns, and type safety detection. Use when working with Sorbet-typed Ruby code."
metadata:
  category: languages
---

# Sorbet

Apply these patterns when writing, reviewing, or refactoring Sorbet-typed Ruby. Load the `ruby` skill alongside this one.

## Detection Patterns

### Types

```bash
# T.untyped hotspots
rg "T\.untyped" --type ruby
rg "T::Hash\[.*T\.untyped\]" --type ruby  # weak hash types
rg "T\.any\(" --type ruby  # union types that could be narrower

# Strictness gaps
rg "typed: false|typed: ignore" --type ruby  # files to upgrade
rg "typed: true" --type ruby  # candidates for strict

# Missing type annotations
rg "^\s+@\w+\s*=" --type ruby  # instance vars without T.let
rg "def \w+\(" --type ruby  # methods (check for missing sig)

# Weak patterns
rg "T\.must\(" --type ruby  # risky nil assertions
rg "T\.cast\(" --type ruby  # forced casts
rg "T\.unsafe\(" --type ruby  # escape hatches

# Boolean parameters (boolean blindness)
rg "T::Boolean" --type ruby  # boolean params in sigs
rg "params\([^)]*: T::Boolean" --type ruby
```

### Tests

```bash
# Sorbet itself catches type errors
srb tc

# Check strictness distribution
rg "^# typed:" --type ruby -o | sort | uniq -c

# Find methods without sigs in strict files
rg -l "typed: strict" --type ruby | xargs -I{} rg "^\s+def " {} | head -20
```

## Idiomatic Sorbet

### T::Struct Over Hashes

```ruby
# Hash with untyped values:
sig { params(opts: T::Hash[Symbol, T.untyped]).void }
def initialize(opts); end  # →

# Typed struct with explicit fields:
class Options < T::Struct
  const :timeout, Integer
  const :retries, Integer, default: 3
end
sig { params(opts: Options).void }
def initialize(opts); end
```

### Type Instance Variables

```ruby
# Untyped instance variable:
def initialize(name)
  @name = name
end  # →

# Typed in initialize:
sig { params(name: String).void }
def initialize(name)
  @name = T.let(name, String)
end

# Lazy initialization:
sig { returns(User) }
def current_user
  @current_user ||= T.let(find_user, T.nilable(User))
  T.must(@current_user)
end
```

### Typed Collections

```ruby
# Bare generic (defaults to T.untyped elements):
sig { returns(Array) }
def names; end  # →

# Explicit element type:
sig { returns(T::Array[String]) }
def names; end

# Hash with specific types:
sig { returns(T::Hash[Symbol, Integer]) }
def counts; end

# Set:
sig { returns(T::Set[User]) }
def active_users; end
```

### Typed Blocks

```ruby
# Block without type:
def each_item(&blk)
  items.each(&blk)
end  # →

# Typed block parameter:
sig { params(blk: T.proc.params(item: Item).void).void }
def each_item(&blk)
  items.each(&blk)
end

# Block with return value:
sig { params(blk: T.proc.params(x: Integer).returns(String)).returns(T::Array[String]) }
def map_items(&blk)
  items.map(&blk)
end
```

### Sealed Modules for Sum Types

```ruby
# Unstructured status handling:
case status
when :pending then ...
when :complete then ...
end  # →

# Sealed module with exhaustive matching:
module Status
  extend T::Helpers
  sealed!

  class Pending < T::Struct; include Status; end
  class Complete < T::Struct
    include Status
    const :result, String
  end
end

sig { params(status: Status).void }
def handle(status)
  case status
  when Status::Pending then handle_pending
  when Status::Complete then handle_complete(status.result)
  else T.absurd(status)  # compile error if cases incomplete
  end
end
```

### Handle Dynamic Data at Boundaries

```ruby
# JSON parsing - accept untyped at boundary:
sig { params(json: T::Hash[String, T.untyped]).returns(User) }
def from_json(json)
  name = json.fetch('name')
  email = json.fetch('email')

  # Narrow types with flow-sensitive checks
  raise ArgumentError unless name.is_a?(String)
  raise ArgumentError unless email.is_a?(String)

  User.new(name: name, email: email)
end
```

### Avoid T.must When Possible

```ruby
# Risky - crashes if nil:
value = T.must(hash[:key])  # →

# Safe - explicit error or default:
value = hash.fetch(:key)  # raises KeyError
value = hash.fetch(:key, default)  # with fallback

# Flow-sensitive narrowing:
value = hash[:key]
return unless value
# value is now non-nil here
```

### Strictness Upgrade Path

```ruby
# Start: typed: false
# → typed: true (enables type errors, sigs optional)
# → typed: strict (sigs required, no implicit T.untyped)
# → typed: strong (T.untyped forbidden entirely)

# In strict files, all methods need sigs:
# typed: strict

sig { params(x: Integer, y: Integer).returns(Integer) }
def add(x, y)
  x + y
end
```

### Boolean Blindness → T::Enum

```ruby
# Boolean parameter hides intent:
sig { params(user: User, urgent: T::Boolean).void }
def send_email(user, urgent:); end
send_email(user, urgent: true)  # what does true mean? →

# Use T::Enum for self-documenting call sites:
class Priority < T::Enum
  enums do
    Normal = new
    Urgent = new
  end
end

sig { params(user: User, priority: Priority).void }
def send_email(user, priority: Priority::Normal); end
send_email(user, priority: Priority::Urgent)  # clear intent

# T::Enum supports exhaustive matching:
sig { params(priority: Priority).returns(Integer) }
def delay_seconds(priority)
  case priority
  when Priority::Normal then 300
  when Priority::Urgent then 0
  else T.absurd(priority)
  end
end
```

### Parse, Don't Validate

```ruby
# Validate then pass raw hash around:
sig { params(params: T::Hash[Symbol, T.untyped]).void }
def process(params)
  raise ArgumentError unless valid_email?(params[:email])
  # params[:email] is still T.untyped... →

# Parse into T::Struct at boundary:
class UserInput < T::Struct
  const :email, String
  const :age, Integer

  sig { params(params: T::Hash[String, T.untyped]).returns(UserInput) }
  def self.parse(params)
    email = params.fetch('email')
    age = params.fetch('age')
    raise ArgumentError unless email.is_a?(String) && email.match?(EMAIL_REGEX)
    raise ArgumentError unless age.is_a?(Integer) && age > 0
    new(email:, age:)
  end
end

sig { params(input: UserInput).void }
def process(input)
  # input.email is String, input.age is Integer - guaranteed
end
```
