---
name: react
description: Use when working on React components and React-facing TypeScript patterns (events, wrapper APIs, component contracts, Formik, TanStack).
metadata:
  category: languages
---

# React Conventions

## Activation

This skill activates when:
- Working on React components (`.tsx`)
- Designing component props and callback contracts
- Handling React event flows
- Wrapping third-party React components
- Using Formik or TanStack in React code

For broad TypeScript casting/null/generic policy, load the `typescript` skill.

## 1. Effects: prefer derivation and event handlers

Before adding `useEffect`, check React guidance: [You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect).

- Derive values during render when they come from props/state.
- Handle user-triggered logic inside event handlers.
- Use effects only to synchronize with external systems (network, subscriptions, DOM APIs, timers).

Bad (redundant derived state in an effect):

```tsx
const [fullName, setFullName] = useState("");
useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);
```

Good (derive in render):

```tsx
const fullName = `${firstName} ${lastName}`;
```

Bad (event-triggered work in an effect):

```tsx
useEffect(() => {
  if (shouldSubmit) submitForm();
}, [shouldSubmit]);
```

Good (run user-triggered work in the event handler):

```tsx
const onSubmit = () => {
  submitForm();
};
```

## 2. React Events

Do not fabricate `React.ChangeEvent`, `KeyboardEvent`, etc. from plain objects.

Use event types only for real DOM/component events.

Prefer data-first callbacks in your component API:

```ts
// Preferred
type ToggleProps = {
  checked: boolean;
  onChange?: (checked: boolean) => void;
};

// Avoid for wrapper APIs unless forwarding raw events directly
type ToggleProps = {
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
};
```

## 3. Wrapper Components

When wrapping third-party components:
- Omit props you control internally
- Re-expose a smaller, clearer API
- Avoid leaking third-party complexity through your wrappers

```ts
type MyToggleProps = Omit<
  React.ComponentProps<typeof Toggle>,
  "checked" | "defaultChecked" | "onChange"
> & {
  checked?: boolean;
  onChange?: (checked: boolean) => void;
};
```

## 4. Component-Level Type Safety Patterns

When resolving React + TS errors:
1. Explain mismatch in plain language
2. Identify root cause at component boundary (props, callback shape, inferred generics)
3. Change component contracts toward explicit, value-shaped APIs
4. Keep adapters local when integrating awkward third-party component types

Prefer explicit prop contracts over ad-hoc inline object shapes for reusable components.

## 5. Component Design

- Prefer small, focused, reusable components over large multi-purpose components.
- Prefer composition and clear data flow over duplicated state and prop soup.
- Reuse existing design-system primitives and styling patterns before inventing new ones.
- If the codebase is doing something unusual and the correct React approach is unclear, check current official React guidance before changing direction.

## Verification checklist

Before adding `useEffect`, verify:
- Can this value be derived during render from existing props/state?
- Can this logic run directly in the event handler that triggers it?
- Is this effect truly synchronizing with an external system?

## Appendices

For library-specific patterns, see:
- `formik.md` - Formik form handling patterns
- `tanstack.md` - TanStack Query, Table, and Router patterns
