---
name: interview-command
description: Start technical discovery interview before coding
argument-hint: [topic or feature]
---

# Interview Mode: $ARGUMENTS

Start a deep-dive technical discovery session for: $ARGUMENTS

## Instructions

**STOP.** Do not start coding yet.

Before writing any implementation code, conduct a thorough technical interview to uncover hidden requirements and technical trade-offs.

## Interview Phase

Use the `AskUserQuestion` tool to interview the user. Ask about:

1. **Functional Requirements**
   - What exactly should this feature do?
   - What are the inputs and outputs?
   - What are the success criteria?

2. **UI/UX Requirements**
   - How should users interact with this?
   - What feedback should users see?
   - Error states and edge cases?

3. **Technical Constraints**
   - Integration with existing code?
   - Performance requirements?
   - Security considerations?

4. **Edge Cases**
   - What happens when...?
   - How should the system behave if...?
   - What's the fallback when...?

5. **Scope Boundaries**
   - What's explicitly NOT included?
   - What can we defer to a future iteration?

## Deep Questions

Challenge the user's initial assumptions:
- "What happens if the user does X instead of Y?"
- "How should this behave on slow connections?"
- "What's the expected data volume?"
- "Who else might use this feature?"

## Spec Creation

Once the interview is complete, summarize everything into a specification:

```markdown
# Feature Specification: [Feature Name]

## Requirements
- Requirement 1
- Requirement 2

## Technical Approach
- How we'll implement this

## Edge Cases
- Edge case 1 and how we handle it

## Out of Scope
- Items explicitly excluded

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

## Confirmation

Only after the spec is reviewed and approved should you proceed to implementation.
