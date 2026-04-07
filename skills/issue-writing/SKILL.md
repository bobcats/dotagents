---
name: issue-writing
description: Write high-quality feature/task issues using user-story language, INVEST, decomposition, and testable acceptance criteria.
metadata:
  category: workflow
---

# Issue Writing

Use this skill before creating issues in any tracker.

## Core Distinction: Feature vs Task

| Aspect | Feature (User Story) | Task |
|---|---|---|
| Focus | User/business value | Technical implementation |
| Language | User terms | Engineering terms |
| Question | "What can users do?" | "What code will we write?" |

## User Story Format (Features)

Preferred format:

`As a [role], I want [goal], so that [benefit].`

Good:
- "As a returning user, I can sign in with Google so that I don't need another password."

Bad:
- "Add OAuth integration" (implementation, not user value)

## Story Quality Checks

### INVEST

- **I**ndependent
- **N**egotiable
- **V**aluable
- **E**stimable
- **S**mall
- **T**estable

If a story fails INVEST, split or rewrite it.

### 3 C's

Every story should support:
- **Card** (brief written placeholder)
- **Conversation** (discussion to refine details)
- **Confirmation** (clear acceptance checks)

## Hierarchy and Decomposition

Use a hierarchy like:

```text
Epic
└── Feature
    └── Task
        └── Subtask
```

Decompose when work is too large, crosses systems, or needs progress checkpoints.

## Acceptance Criteria Patterns

### Checkbox Scenarios

- [ ] User receives tracking email after purchase
- [ ] Tracking page shows current shipment status

### Given-When-Then

- [ ] Given I am logged in, when I place an order, then I receive confirmation email
- [ ] Given I have a tracking number, when I open tracking page, then I see latest status

Criteria should be specific, testable, and tied to user value.

## Implementation Pipeline

After issues are created and prioritized:

- Use the `writing-plans` skill to create an implementation plan from the issue
- Use the `executing-plans` skill to implement the plan task-by-task
- For issues that need design exploration first, use the `brainstorming` skill
