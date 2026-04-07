---
name: go
description: "Idiomatic Go patterns, anti-patterns, and code quality detection. Use when writing, reviewing, or refactoring Go code."
metadata:
  category: languages
---

# Go

Apply these patterns when writing, reviewing, or refactoring Go code.

## Detection Patterns

### Dead Code

```bash
rg "^func \w+" --type go -o | sort | uniq
rg "^//.*\n//.*\n//" --multiline --type go  # commented blocks
staticcheck ./...  # reports unused code
```

### Types

```bash
# Empty interface (weak typing)
rg "interface\{\}" --type go
rg "any\b" --type go  # same as interface{} (1.18+)
rg "map\[string\]interface\{\}|map\[string\]any" --type go

# Type assertions without ok check
rg "\.\(\w+\)(?!\s*;|\s*,)" --type go

# Boolean parameters (boolean blindness)
rg "func \w+\([^)]*bool[,)]" --type go
rg "\w+\(true\)|\w+\(false\)" --type go  # boolean literals at call sites
```

### Tests

```bash
rg "t\.Skip\(" --type go
rg "func Test" --type go -c | sort -t: -k2 -n
go test -cover ./...  # coverage
```

### Performance

```bash
rg "append\(.*,.*\.\.\.\)" --type go  # slice append in loop
rg "string\(.*\[\]byte" --type go  # repeated conversions
rg "for.*range.*\{[^}]*go\s" --type go  # goroutine in loop (closure bug)
```

## Idiomatic Go

### Error Handling

```go
// Always check errors (never discard with _):
result, _ := doSomething()  // DON'T

result, err := doSomething()
if err != nil {
    return fmt.Errorf("doing something: %w", err)  // wrap with context
}

// Use errors.Is for sentinel errors:
if err == ErrNotFound { }  // DON'T
if errors.Is(err, ErrNotFound) { }  // correct

// Use errors.As for error types:
var pathErr *os.PathError
if errors.As(err, &pathErr) {
    fmt.Println(pathErr.Path)
}

// Error strings: lowercase, no punctuation
return fmt.Errorf("connection failed")  // correct
return fmt.Errorf("Connection failed.")  // DON'T

// Custom error types for context:
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("%s: %s", e.Field, e.Message)
}
```

### Small Interfaces

```go
// Go Proverb: "The bigger the interface, the weaker the abstraction"

// Small, focused interfaces (1-2 methods):
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

// Compose by embedding:
type ReadWriter interface {
    Reader
    Writer
}

// Accept interfaces, return structs:
func Process(r io.Reader) (*Result, error) { ... }

// Define interfaces at point of use:
type UserStore interface {
    Find(id string) (*User, error)
}

func NewHandler(store UserStore) *Handler { ... }
```

### Generics (1.18+)

```go
// Type parameters with constraints:
func Map[T, U any](items []T, fn func(T) U) []U {
    result := make([]U, len(items))
    for i, item := range items {
        result[i] = fn(item)
    }
    return result
}

// Built-in constraints:
// any = interface{} (accepts anything)
// comparable = supports == and != (for map keys)

// Custom constraints:
type Number interface {
    ~int | ~int64 | ~float64
}

func Sum[T Number](items []T) T {
    var total T
    for _, item := range items {
        total += item
    }
    return total
}

// When to use generics vs interfaces:
// - Generics: type-safe operations over concrete types
// - Interfaces: behavior abstraction (methods matter)
```

### Resource Cleanup

```go
// defer for cleanup:
f, err := os.Open(path)
if err != nil {
    return err
}
defer f.Close()

// defer runs in LIFO order:
defer fmt.Println("first")
defer fmt.Println("second")
// prints: second, first

// Capture loop variable for defer:
for _, f := range files {
    f := f  // shadow to capture current value
    defer f.Close()
}
```

### Concurrency Patterns

```go
// Channel for signaling (zero-size):
done := make(chan struct{})
close(done)  // broadcast to all receivers

// Select with timeout:
select {
case result := <-ch:
    process(result)
case <-time.After(5 * time.Second):
    return errors.New("timeout")
}

// sync.Once for lazy init:
var (
    instance *Config
    once     sync.Once
)

func GetConfig() *Config {
    once.Do(func() { instance = loadConfig() })
    return instance
}

// Context for cancellation:
func DoWork(ctx context.Context) error {
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
        // continue work
    }
    return nil
}
```

### Table-Driven Tests

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive", 1, 2, 3},
        {"zero", 0, 0, 0},
        {"negative", -1, 1, 0},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := Add(tt.a, tt.b)
            if got != tt.expected {
                t.Errorf("Add(%d, %d) = %d, want %d",
                    tt.a, tt.b, got, tt.expected)
            }
        })
    }
}
```

### Go Proverbs

```go
// "Clear is better than clever"
// Prefer readable code over compact tricks

// "A little copying is better than a little dependency"
// Don't import a package for one small function

// "Make the zero value useful"
type Buffer struct {
    data []byte
}
// Zero Buffer{} is ready to use, no constructor needed

// "Don't communicate by sharing memory, share memory by communicating"
// Use channels instead of mutexes when possible
```

### Boolean Blindness

```go
// Boolean parameter hides intent:
func SendEmail(user User, urgent bool) { }
SendEmail(user, true)  // what does true mean? →

// Use typed constant (iota enum) for self-documenting call sites:
type Priority int

const (
	PriorityNormal Priority = iota
	PriorityUrgent
)

func SendEmail(user User, priority Priority) { }
SendEmail(user, PriorityUrgent)  // clear intent

// String method for debugging:
func (p Priority) String() string {
	switch p {
	case PriorityNormal:
		return "normal"
	case PriorityUrgent:
		return "urgent"
	default:
		return fmt.Sprintf("Priority(%d)", p)
	}
}
```

### Parse, Don't Validate

```go
// Validating then using raw map:
func Process(data map[string]any) error {
	email, ok := data["email"].(string)
	if !ok {
		return errors.New("invalid email")
	}
	// email is string but still passing raw map around... →

// Parse into struct at boundary:
type UserInput struct {
	Email string
	Age   int
}

func ParseUserInput(data map[string]any) (UserInput, error) {
	email, ok := data["email"].(string)
	if !ok || !strings.Contains(email, "@") {
		return UserInput{}, errors.New("invalid email")
	}
	age, ok := data["age"].(float64)  // JSON numbers are float64
	if !ok || age <= 0 {
		return UserInput{}, errors.New("invalid age")
	}
	return UserInput{Email: email, Age: int(age)}, nil
}

func Process(input UserInput) error {
	// input.Email and input.Age are guaranteed valid
	return nil
}
```
