# Streamline Agent Instructions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep long-term Agent discipline in `AGENTS.md` and move detection architecture principles to `docs/architecture_principles.md` without changing policy.

**Architecture:** `AGENTS.md` remains the always-loaded Agent contract. Architecture design lives in a linked document that must be read before detector-architecture changes.

**Tech Stack:** Markdown documentation only. No Python, dataset, test, or experiment changes.

**Spec:** User documentation-refactor request plus existing `AGENTS.md` policy.

## Global Constraints

- Do not modify Python source, datasets, tests, or experiment results.
- Do not weaken current core constraints.
- Target about 150-250 lines in `AGENTS.md` without deleting required rules.
- Raw integrity command must be copied from existing code, not guessed.
- Individual internal tasks must not push; only the user-authorized stage may commit and push after verification.
- Do not enter any Phase development.

---

### Task 1: Split architecture principles and compact AGENTS.md

**Files:**
- Create: `docs/architecture_principles.md`
- Modify: `AGENTS.md`
- Create: `docs/superpowers/plans/2026-09-11-streamline-agent-instructions.md`

**Interfaces:**
- Consumes: current `AGENTS.md` policy text
- Produces: compact Agent discipline file plus architecture document linked from `AGENTS.md`

- [x] **Step 1: Recover workspace after stream disconnect**
- [x] **Step 2: Move architecture sections without weakening them**
- [x] **Step 3: Rewrite AGENTS.md to keep required long-term rules**
- [x] **Step 4: Independent Spec Review**
- [x] **Step 5: Run git diff --check, git diff, git status**
- [ ] **Step 6: Commit `docs: streamline agent instructions` and push main**
