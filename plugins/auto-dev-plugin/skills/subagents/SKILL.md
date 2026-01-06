---
name: subagents
description: Guide for using Claude Code subagents effectively. Use when deciding whether to delegate a task to a subagent or handle it directly.
---

# Subagents Guide

Subagents are autonomous Claude instances that work independently on well-defined tasks. They have their own context, tools, and completion criteria.

## When to Use Subagents

### Good Candidates
- **Multi-file coding tasks** - Features requiring changes across several files
- **Well-defined implementations** - Clear requirements with known acceptance criteria
- **Test-driven development** - Tasks where tests can verify correctness
- **Refactoring work** - Restructuring code with existing test coverage
- **Bug fixes** - Issues with reproducible test cases
- **New features** - Complete features with clear specifications

### Poor Candidates
- **Exploratory questions** - "How does this work?"
- **Quick explanations** - "What does this function do?"
- **Code review requests** - "Review this change"
- **Architecture discussions** - "Should we use REST or GraphQL?"
- **Git operations** - Commits, pushes, branch management
- **Ambiguous requirements** - Tasks needing back-and-forth clarification

## The `coder` Subagent

**Purpose:** Autonomous coding agent that implements features and fixes bugs

**Tools:** Read, Write, Edit, Bash, Grep, Glob

**Workflow:**
1. Reads relevant files to understand the codebase
2. Plans the implementation in small steps
3. Makes changes incrementally
4. Runs tests after significant changes
5. Iterates until all tests pass
6. Reports completion with summary

**Test Gate:** When the coder completes, the SubagentStop hook runs tests. If tests fail, the subagent is blocked and must fix issues before completion.

## How to Invoke

### Automatic Classification
The UserPromptSubmit hook auto-classifies prompts. Coding tasks are automatically suggested for subagent delegation.

### Explicit Request
Prefix your prompt with `subagent:` to force delegation:
```
subagent: implement user authentication
```

### Parallel Execution
For multiple independent coding tasks, subagents can run in parallel:
```
1. Add user profile page
2. Implement password reset
3. Create admin dashboard
```
The classifier will detect these as separate coding tasks and suggest parallel execution.

## Best Practices

1. **Provide clear requirements** - Specific, actionable descriptions
2. **Specify acceptance criteria** - What does "done" look like?
3. **Reference related files** - Help the agent find context quickly
4. **Set boundaries** - Which parts of the codebase to touch
5. **Trust the tests** - If tests pass, the implementation is correct

## Example Prompts

### Feature Implementation
```
subagent: Add search functionality to the products page

Requirements:
- Search input with debounced API calls
- Display results in existing product grid
- Handle empty state and loading state
- Add tests for search logic

Files: src/pages/Products.tsx, src/api/products.ts
```

### Bug Fix
```
Fix the issue where form validation doesn't trigger on blur

Steps to reproduce:
1. Go to contact form
2. Click into email field, then click out
3. No validation error appears (should show "Email required")

Related: src/components/ContactForm.tsx
```
