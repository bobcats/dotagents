---
name: typescript
description: "Idiomatic TypeScript patterns, type safety policies, and code quality detection. Use when writing, reviewing, or refactoring TypeScript code."
metadata:
  category: languages
---

# TypeScript

Apply these patterns when writing, reviewing, or refactoring TypeScript code.

## Type Safety Policies

### Cast Avoidance Policy

Avoid escape hatches except at tightly-scoped, documented interop boundaries:
- `as any`
- `as unknown as`
- `@ts-ignore` / `@ts-expect-error`

Preferred order:
1. Fix the source types
2. Add narrowing/type guards
3. Use generics to express intent
4. Use a minimal adapter cast only when third-party typings are wrong

### Null Narrowing Policy

Assume `strictNullChecks` is enabled and write control flow accordingly.

Prefer:
- early returns for nullable values
- `if`/`switch`/`in` narrowing
- `??` over `||` for defaults where `0`, `false`, or `""` are valid

Avoid non-null assertions (`!`) unless correctness is proven in nearby control flow.

### Discriminated Union Handling Policy

Represent variants as discriminated union types and handle via exhaustive switches.

Requirements:
- include a stable discriminant (`kind`, `type`, etc.)
- narrow through control flow, not casts
- include `never` exhaustiveness checks when branching

### Generic-Parameter-Over-Casting Policy

Prefer explicit generic parameters over result casting.

Good:
- `parseThing<MyType>(input)`

Avoid:
- `parseThing(input) as MyType`

If generics are hard to express, improve API signatures before adding casts.

## Detection Patterns

### Dead Code

```bash
rg "export (const|function|class|type|interface) \w+" --type ts -o
rg "^//.*\n//.*\n//" --multiline --type ts  # commented blocks
```

### Types

```bash
# any violations
rg ": any\b|as any" --type ts
rg "as unknown as" --type ts  # double-cast escape hatch
rg "@ts-ignore|@ts-expect-error" --type ts
rg "Record<string, any>|\bobject\b" --type ts

# Weak patterns
rg "!\." --type ts  # non-null assertions
rg "\|\| \[\]|\|\| \{\}|\|\| 0|\|\| \"\"" --type ts  # falsy defaults (use ??)

# Boolean parameters (boolean blindness)
rg "\w+\(true\)|\w+\(false\)" --type ts  # boolean literals at call sites
rg ": boolean[,)]" --type ts  # boolean params in signatures
```

### Tests

```bash
rg "(xit|xdescribe|xtest|\.skip|\.todo)" --glob "*.test.ts" --glob "*.spec.ts"
rg "(expect|assert)" --type ts -c | sort -t: -k2 -n
```

### Performance

```bash
rg "\.map\(.*\)\.map\(|\.filter\(.*\)\.map\(" --type ts  # single pass
rg "await.*\n.*await.*\n.*await" --multiline --type ts  # Promise.all candidate
```

## Idiomatic TypeScript

### Discriminated Unions with Exhaustive Checking

```typescript
// Discriminated union with literal discriminant
type Result<T> =
  | { ok: true; value: T }
  | { ok: false; error: Error };

function handle(result: Result<User>) {
  if (result.ok) {
    console.log(result.value);  // narrowed to { ok: true; value: User }
  } else {
    console.error(result.error);  // narrowed to { ok: false; error: Error }
  }
}

// Exhaustive switch with never
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "square"; size: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle": return Math.PI * shape.radius ** 2;
    case "square": return shape.size ** 2;
    default:
      const _exhaustive: never = shape;
      return _exhaustive;  // compile error if cases incomplete
  }
}
```

### const Assertions and satisfies

```typescript
// const assertion preserves literal types
const COLORS = ["red", "green", "blue"] as const;
type Color = typeof COLORS[number];  // "red" | "green" | "blue"

// satisfies: type check without widening
const config = {
  port: 3000,
  host: "localhost",
} satisfies ServerConfig;
// config.port is number, not number | undefined

// Combine for maximum benefit
const routes = {
  home: "/",
  users: "/users",
  user: "/users/:id",
} as const satisfies Record<string, string>;
// Type-checked AND literal types preserved
```

### unknown Over any

```typescript
// any disables type checking (avoid):
function parse(json: string): any {
  return JSON.parse(json);
}
const data = parse("{}");
data.anything.goes;  // no error, crashes at runtime

// unknown requires narrowing (prefer):
function parse(json: string): unknown {
  return JSON.parse(json);
}
const data = parse("{}");
// data.anything  // compile error

// Narrow with type guards
if (typeof data === "object" && data !== null && "name" in data) {
  console.log(data.name);  // safe
}
```

### Type Guards

```typescript
// Built-in narrowing
if (typeof x === "string") { /* x is string */ }
if (x instanceof Date) { /* x is Date */ }
if ("kind" in x) { /* x has kind property */ }

// User-defined type guard
function isUser(x: unknown): x is User {
  return typeof x === "object" && x !== null && "id" in x && "name" in x;
}

if (isUser(data)) {
  console.log(data.name);  // data is User
}

// Assertion function (throws if invalid)
function assertUser(x: unknown): asserts x is User {
  if (!isUser(x)) throw new Error("Not a user");
}

assertUser(data);
console.log(data.name);  // data is User after assertion
```

### Nullish Coalescing Over Logical Or

```typescript
// || treats 0, "", false as falsy (often wrong):
const port = config.port || 3000;  // 0 becomes 3000

// ?? only treats null/undefined as nullish (usually correct):
const port = config.port ?? 3000;  // 0 stays 0

// Optional chaining + nullish coalescing
const name = user?.profile?.name ?? "Anonymous";
```

### Utility Types

```typescript
// Extract return type
type UserResult = ReturnType<typeof getUser>;

// Extract parameters
type GetUserParams = Parameters<typeof getUser>;

// Make all properties optional
type PartialUser = Partial<User>;

// Make all properties required
type RequiredUser = Required<User>;

// Pick specific properties
type UserName = Pick<User, "firstName" | "lastName">;

// Omit specific properties
type UserWithoutPassword = Omit<User, "password">;

// Extract from union
type StringOrNumber = string | number | boolean;
type JustStrings = Extract<StringOrNumber, string>;  // string

// Exclude from union
type NoStrings = Exclude<StringOrNumber, string>;  // number | boolean
```

### Template Literal Types

```typescript
// Type-safe event names
type EventName = `on${Capitalize<string>}`;
// "onClick", "onHover", etc.

// Route parameters
type Route = `/users/${string}` | `/posts/${string}`;

// Infer from template
type ExtractId<T> = T extends `/users/${infer Id}` ? Id : never;
type UserId = ExtractId<"/users/123">;  // "123"
```

### Map/Set Over Object Literals

```typescript
// Object literal with string keys (weak typing):
const cache: { [key: string]: Value } = {};
cache["key"] = value;  // no type safety on keys

// Map for dynamic keys (better):
const cache = new Map<UserId, User>();
cache.set(id, user);  // type-safe
cache.get(id);  // User | undefined

// Set for unique values:
const visited = new Set<string>();
visited.add(url);
visited.has(url);  // boolean
```

### Promise.all for Independent Async Ops

```typescript
// Sequential (slow):
const user = await getUser(id);
const posts = await getPosts(id);
const comments = await getComments(id);

// Parallel (fast):
const [user, posts, comments] = await Promise.all([
  getUser(id),
  getPosts(id),
  getComments(id),
]);

// With error handling per-promise:
const results = await Promise.allSettled([
  getUser(id),
  getPosts(id),
]);
// results[0].status === "fulfilled" | "rejected"
```

### Boolean Blindness

```typescript
// Boolean parameter hides intent:
function sendEmail(user: User, urgent: boolean): void { }
sendEmail(user, true);  // what does true mean? →

// Use union type for self-documenting call sites:
type Priority = "normal" | "urgent";
function sendEmail(user: User, priority: Priority): void { }
sendEmail(user, "urgent");  // clear intent

// Or use const object for namespacing:
const Priority = {
  Normal: "normal",
  Urgent: "urgent",
} as const;
type Priority = typeof Priority[keyof typeof Priority];

sendEmail(user, Priority.Urgent);
```

### Parse, Don't Validate

```typescript
// Validating then using raw data:
function process(data: unknown): void {
  if (typeof data !== "object" || data === null) throw new Error();
  if (!("email" in data) || typeof data.email !== "string") throw new Error();
  // data is still awkward to use... →

// Parse into typed structure at boundary:
interface User {
  email: string;
  age: number;
}

function parseUser(data: unknown): User {
  if (typeof data !== "object" || data === null) {
    throw new Error("expected object");
  }
  if (!("email" in data) || typeof data.email !== "string") {
    throw new Error("invalid email");
  }
  if (!("age" in data) || typeof data.age !== "number" || data.age <= 0) {
    throw new Error("invalid age");
  }
  return { email: data.email, age: data.age };
}

function process(user: User): void {
  // user.email is string, user.age is number - guaranteed
}

// Or use zod for declarative parsing:
const UserSchema = z.object({
  email: z.string().email(),
  age: z.number().positive(),
});
type User = z.infer<typeof UserSchema>;

const user = UserSchema.parse(data);  // throws if invalid
```
