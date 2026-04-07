---
name: executing-plans
description: Use when you have a written implementation plan to execute
metadata:
  category: superpowers
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** In interactive sessions, state you're using this skill in one short sentence. In non-interactive execution, skip ceremony and start the work.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Proceed to execution

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed
5. Continue to next task

### Step 3: Complete

After all tasks complete and verified:
- Run final verifications as specified in the plan
- Summarize completed work and verification output
- Keep final report terse: changed files + verification result only
- Include exact commands you ran for verification (and commit command when a commit is required)
- End after the required summary; do not add optional next-step offers or questions

## Execution Efficiency Rules

- Do exactly what the plan requires; do not add optional improvements or extra tasks.
- Keep all status updates and final output concise (no long narrative, no "If you want, I can..." add-ons).
- Run only the verifications explicitly required by the plan.
- Do not perform extra exploratory commands once required verifications pass.

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

When blocked, include the failing command in your blocker report.

**Don't force through blockers** - stop and ask.

## Remember
- Follow plan steps exactly
- Don't skip verifications
- Stop when blocked, don't guess
