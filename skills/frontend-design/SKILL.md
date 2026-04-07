---
name: frontend-design
description: Craft premium B2B interfaces - information-dense, predictable, and professional. Invoke before building any user-facing component.
metadata:
  category: languages
---

# Frontend Design

Premium B2B interfaces through refinement, not decoration. Power users live in your interface daily - respect their time and optimize for efficiency.

Apply the mindset of a designer-turned-developer: create professional, cohesive interfaces that feel intentional and refined, even without mockups or design specs.

**IMPORTANT**: Load the `react` skill before writing any TypeScript/React code.

## Activation

This skill activates when:
- Building any user-facing component, page, or interface
- Making visual or interaction design decisions
- Working with frontend code (React, Vue, HTML/CSS)
- User requests UI/UX work or mentions "interface", "component", "page", "design"

## Dependencies

**Invokes:** `react` before writing any TypeScript/React code

---

## Before You Code

### 1. Study the Codebase

Match existing patterns exactly. Your component should feel like it was always there.

- Read 2-3 similar components in the repo
- Note spacing values, color variables, component patterns
- Check for design tokens or style constants

### 2. Understand Context

| Question | Why It Matters |
|----------|----------------|
| What workflow does this support? | Determines information hierarchy |
| What decisions does it enable? | Drives what data to surface |
| Who uses it and how often? | Daily users need density; occasional users need guidance |
| What density do power users need? | Optimize for scanning and comparison |

### 3. Commit to Direction

Before writing code, state your approach:
- Primary user action
- Information hierarchy (what's most scannable)
- Interaction pattern (matches existing or justified deviation)

---

## Design Principles

**CRITICAL**: B2B users are repeat users. They learn your interface. Predictability and consistency matter more than novelty. Same action = same pattern everywhere.

### Information Density

**Tables over cards when comparing data.** Cards waste space and break scanability.

- Dense defaults with expansion options
- Progressive disclosure for complexity, not for hiding
- Every click and scroll must earn its place

### Visual Hierarchy

What's important is immediately obvious.

- One primary CTA per view
- Functional color coding (status, action types) - not decoration
- Clear grouping through whitespace, not dividers

### Typography

Legibility over personality.

- System fonts are acceptable
- Consistent type scale (don't invent sizes)
- Sufficient contrast for long reading sessions

### Spacing

Tight but breathable.

- 4px/8px grid
- Match existing spacing tokens exactly
- Clear grouping through whitespace

### Motion

Animations only for feedback.

- Loading states, transitions, success/error only
- 150-200ms durations maximum
- No gratuitous motion - users are here to work

### Async Search & Filtering

Stale-while-revalidate: keep showing previous results while fetching new ones.

- Initial load (no data yet): show skeleton/spinner
- Subsequent queries: keep old results visible, show subtle inline loading indicator (e.g. spinner in search input)
- Never flash a full loading state between search result sets — it feels jumpy
- Swap results only when new data arrives

### Color

Restrained and functional.

- CSS variables for consistency
- Accent color for primary CTAs only
- Status colors have meaning, not decoration

---

## Constraints

**NEVER sacrifice information density for visual flair.** Avoid hero sections, decorative illustrations, playful animations, marketing-speak in UI copy, and cards when tables would work better. B2B users want to see data, not scroll through whitespace.

Hard blocks. Violating these fails the task.

| Constraint | Why |
|------------|-----|
| No `as any` type casts | Destroys type safety; hides runtime bugs |
| No `@ts-ignore` / `@ts-expect-error` | Suppresses real errors; unmaintainable |
| No fabricated React synthetic events | Runtime crashes; use proper event signatures |
| No hero sections or splash layouts | Wastes viewport on daily users |
| No decorative animations or illustrations | Slows workflows |
| No marketing-speak in UI copy | Power users want clarity, not persuasion |
| No cards when tables work better | Tables enable scanning and comparison |

---

## Implementation Checklist

Before marking UI work complete:

- [ ] Studied existing components for patterns
- [ ] Spacing matches design tokens / existing values
- [ ] Color uses CSS variables, not hardcoded values
- [ ] Typography uses existing scale
- [ ] No decorative elements (illustrations, hero sections, playful animations)
- [ ] Tables used for comparable data, not cards
- [ ] Primary action is immediately obvious
- [ ] Dense by default, expandable where needed
- [ ] `tsc --noEmit` passes (if TypeScript)
- [ ] Renders without console errors

---

## The B2B Standard

Premium B2B feel comes from:
- Precise spacing
- Clear hierarchy
- Consistent patterns
- Polished interactions

**Not from:** Bold aesthetics, memorable visuals, decorative flair.

The best B2B interface is one users don't notice because it just works.
