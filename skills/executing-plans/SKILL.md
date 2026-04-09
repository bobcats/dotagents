---
name: executing-plans
description: Use when you have a written implementation plan to execute
metadata:
  category: superpowers
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. Check plan structure before execution:
   - `- [ ]` items are executable work
   - sections like `## Follow-ups`, `## Deferred Ideas`, and `## Out of Scope` are non-executable context
   - if a checkbox item is labeled optional/conditional (`Optional`, `Maybe`, `If time`, `If desired`, `Stretch`, etc.), treat that as a plan bug and stop for clarification
4. If concerns: Raise them with your human partner before starting
5. If no concerns: Proceed to execution

### Step 2: Execute Tasks

Work through `- [ ]` items **one at a time, sequentially**:
1. Pick the next unchecked `- [ ]` item from the executable portion of the plan
2. Mark as in_progress
3. Follow each step exactly (plan has bite-sized steps)
4. Run verifications as specified
5. Check it off in the plan file (`- [ ]` → `- [x]`) before moving on
6. Commit at stable checkpoint when the item closes (do not accumulate big-bang changes)
   - Use the `semantic-commit` skill for commit messages
7. If blocked: Stop and ask for help (don't guess)
   - If blocked by a bug: use the `systematic-debugging` skill, then return to this task
8. Continue to next item

**Hard gate:** Do NOT start the next `- [ ]` item until the current one is checked off. One item, verified, checked off, then next. No batching, no parallelizing, no "I'll check these off together at the end."

### Step 3: Complete

After all tasks complete and verified:
- Use the `verification-before-completion` skill for final checks
- If the plan included documentation tasks, use the `document-writing` skill (with `writing-clearly-and-concisely` for prose quality)
- Summarize completed work and verification output

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing progress on the current task
- Plan mixes optional/conditional language into executable checkbox items
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Only execute required checkbox items
- Treat follow-up/deferred/out-of-scope sections as non-executable unless the human explicitly promotes them into a new plan
- If optional language appears inside executable checkbox items, stop and get the plan fixed before continuing
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
