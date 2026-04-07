---
name: rust
description: "Idiomatic Rust patterns, anti-patterns, and code quality detection. Use when writing, reviewing, or refactoring Rust code."
metadata:
  category: languages
---

# Rust

Apply these patterns when writing, reviewing, or refactoring Rust code.

## Detection Patterns

### Dead Code

```bash
rg "^(pub )?(fn|struct|enum|trait|type|const) \w+" --type rust -o | sort | uniq
rg "#\[allow\(dead_code\)\]" --type rust  # explicit allowances
rg "^//.*\n//.*\n//" --multiline --type rust  # commented blocks
cargo clippy -- -W clippy::pedantic  # reports unused code
```

### Types

```bash
# Type erasure (weak typing)
rg "Box<dyn Any>" --type rust
rg "HashMap<String, Value>|serde_json::Value" --type rust  # untyped JSON
rg "#\[allow\(clippy::type_complexity\)\]" --type rust

# Potential panics
rg "\.unwrap\(\)" --type rust
rg "\.expect\(" --type rust
rg "panic!|todo!|unimplemented!" --type rust

# Boolean parameters (boolean blindness)
rg "fn \w+\([^)]*: bool[,)]" --type rust
rg "\w+\(true\)|\w+\(false\)" --type rust  # boolean literals at call sites
```

### Tests

```bash
rg "#\[ignore\]" --type rust
rg "assert!|assert_eq!" --type rust -c | sort -t: -k2 -n
cargo test --no-run  # check tests compile
```

### Performance

```bash
rg "\.collect::<Vec<" --type rust  # collect then iterate
rg "\.clone\(\)" --type rust  # unnecessary clones
rg "to_string\(\)|to_owned\(\)" --type rust  # in hot paths
rg "Arc::clone|Rc::clone" --type rust  # reference counting overhead
```

## Idiomatic Rust

### Error Handling

```rust
// Use ? operator over match:
let value = match result {
    Ok(v) => v,
    Err(e) => return Err(e),
};  // →
let value = result?;

// thiserror for library errors (typed, From derives):
#[derive(Debug, thiserror::Error)]
pub enum MyError {
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("invalid input: {0}")]
    InvalidInput(String),
}

// anyhow for application errors (context chaining):
use anyhow::{Context, Result};

fn process() -> Result<()> {
    let data = read_file()
        .context("failed to read config")?;
    Ok(())
}

// Never panic in libraries - return Result
pub fn parse(s: &str) -> Result<Config, ParseError> { ... }  // good
pub fn parse(s: &str) -> Config { s.parse().unwrap() }  // DON'T
```

### Ownership and Borrowing

```rust
// Prefer borrowing over cloning:
fn process(data: &[u8]) { ... }  // borrows
fn process(data: Vec<u8>) { ... }  // takes ownership (only if needed)

// Use &str and &[T] over &String and &Vec<T>:
fn greet(name: &str) { ... }  // accepts String, &str, Cow<str>
fn greet(name: &String) { ... }  // DON'T - only accepts &String

// Minimize mutable reference scope:
let result = {
    let mut data = self.data.borrow_mut();
    data.compute()
};  // mutable borrow ends here

// Interior mutability when needed:
use std::cell::RefCell;
struct Cache {
    data: RefCell<HashMap<K, V>>,
}
```

### Common Trait Implementations

```rust
// Derive common traits (from Rust API Guidelines):
#[derive(Debug, Clone, PartialEq, Eq, Hash, Default)]
pub struct UserId(u64);

// Implement standard conversions:
impl From<u64> for UserId {
    fn from(id: u64) -> Self {
        UserId(id)
    }
}

// Serde for serialization:
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Config {
    pub timeout: u64,
    pub retries: u32,
}

// Default for optional configuration:
impl Default for Config {
    fn default() -> Self {
        Self { timeout: 30, retries: 3 }
    }
}
let config = Config { timeout: 60, ..Default::default() };
```

### Iterator Patterns

```rust
// Iterator chains over loops:
let mut result = Vec::new();
for item in items {
    if item.valid {
        result.push(item.value);
    }
}  // →
let result: Vec<_> = items
    .iter()
    .filter(|x| x.valid)
    .map(|x| x.value)
    .collect();

// Option combinators:
match opt {
    Some(x) => Some(transform(x)),
    None => None,
}  // →
opt.map(transform)

// Early return with ?:
let x = opt?;  // returns None if None

// Fallback with unwrap_or:
let x = opt.unwrap_or(default);
let x = opt.unwrap_or_else(|| expensive_default());
```

### Design Patterns

```rust
// Newtype for type safety (zero-cost):
struct Miles(f64);
struct Kilometers(f64);
// Compiler prevents mixing Miles and Kilometers

// Builder for complex construction:
let server = ServerBuilder::new()
    .port(8080)
    .timeout(Duration::from_secs(30))
    .build()?;

// Typestate for compile-time state machines:
struct Request<State> { ... }
struct Pending;
struct Validated;

impl Request<Pending> {
    fn validate(self) -> Result<Request<Validated>, Error> { ... }
}
impl Request<Validated> {
    fn execute(self) -> Response { ... }  // only callable after validate
}
```

### Pattern Matching

```rust
// if let for single pattern:
match option {
    Some(x) => do_something(x),
    None => {},
}  // →
if let Some(x) = option {
    do_something(x);
}

// let else for early return (Rust 1.65+):
let Some(x) = option else {
    return Err(Error::NotFound);
};

// @ bindings:
match value {
    n @ 1..=10 => println!("small: {}", n),
    n => println!("large: {}", n),
}
```

### Rust Philosophy

```rust
// Zero-cost abstractions - abstractions compile away:
items.iter().map(|x| x * 2).collect()  // as fast as manual loop

// Make illegal states unrepresentable:
enum ConnectionState {
    Disconnected,
    Connected { socket: TcpStream },  // socket only exists when connected
}

// Parse, don't validate (from Alexis King):
// Instead of validating and passing raw data,
// parse into typed structures that can't be invalid
fn parse_email(s: &str) -> Result<Email, ParseError> { ... }

// Prefer compile-time over runtime checks:
// Use generics and traits to catch errors at compile time

// Explicit over implicit:
// No hidden allocations, no implicit conversions, errors are values
```

### Boolean Blindness

```rust
// Boolean parameter hides intent:
fn send_email(user: &User, urgent: bool) { }
send_email(&user, true);  // what does true mean? →

// Use enum for self-documenting call sites:
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Priority {
    Normal,
    Urgent,
}

fn send_email(user: &User, priority: Priority) { }
send_email(&user, Priority::Urgent);  // clear intent

// Enums enable exhaustive matching:
fn delay_seconds(priority: Priority) -> u64 {
    match priority {
        Priority::Normal => 300,
        Priority::Urgent => 0,
    }  // compiler error if case added without handling
}
```

### Clippy Lints

```bash
# Run clippy
cargo clippy

# With pedantic lints
cargo clippy -- -W clippy::pedantic

# Key lints to enable:
# clippy::unwrap_used - avoid .unwrap()
# clippy::expect_used - avoid .expect()
# clippy::clone_on_ref_ptr - unnecessary Arc/Rc clone
# clippy::cognitive_complexity - function complexity
```
