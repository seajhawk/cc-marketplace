#!/usr/bin/env python3
"""
UserPromptSubmit hook - Classifies prompts to guide Claude's behavior.
Adds context that tells Claude whether to delegate to subagent or answer directly.
Supports multi-request prompts with individual classification per request.

Part of the autonomous-dev plugin.
"""
import json
import sys
import re

# Import activity logger
try:
    from activity_logger import log_prompt_classification
except ImportError:
    def log_prompt_classification(*args, **kwargs): pass

# Patterns indicating quick questions (no coding needed)
QUICK_PATTERNS = [
    r"^(how|what|why|when|where|who|can you|could you|do you|does|is|are)\b.*\?$",
    r"\b(explain|describe|tell me about|what is|what are)\b",
    r"\b(commit|push|pull|merge|readme|doc|documentation)\b",
    r"^(yes|no|ok|thanks|thank you|great|good|perfect|sure|got it)\b",
    r"^(show|list|find|search|grep|where is)\b",
    r"^(hello|hi|hey|greetings)\b",
]

# Patterns indicating coding tasks that should use subagent
CODING_PATTERNS = [
    # Action verb + coding target
    r"\b(implement|create|build|add|fix|refactor|update|change|modify|write|delete|remove|rename|migrate|upgrade)\b.{0,30}\b(function|class|component|feature|bug|code|file|module|test|api|endpoint|page|hook|system|logic|method|service|handler|route|controller|model|schema|validation|form|button|modal|dialog|login|auth|authentication|database|query|table|view|style|css|layout|ui|interface|type|types|config|setting)\b",
    r"\bsubagent:\s",  # Explicit subagent request
    r"\b(develop|program|code up|build out)\b",
    r"\b(new feature|add feature|implement feature)\b",
    r"\b(fix the|fix this|debug|resolve)\b.{0,20}\b(bug|error|issue|problem)\b",
    r"\b(delete|remove)\b.{0,20}\b(old|deprecated|unused)\b",
    r"\b(rename|move)\b.{0,20}\b(to|into|from)\b",
    # Standalone coding action verbs
    r"^(implement|create|build|add|fix|refactor)\b",
]

# Patterns for splitting multi-request prompts
EXPLICIT_DELIMITERS = [
    r"^\s*\d+\.\s+",           # 1. 2. 3.
    r"^\s*\d+\)\s+",           # 1) 2) 3)
    r"^\s*[a-z]\.\s+",         # a. b. c.
    r"^\s*[a-z]\)\s+",         # a) b) c)
    r"^\s*-\s+",               # - bullet
    r"^\s*\*\s+",              # * bullet
    r"^\s*•\s+",               # bullet
]

IMPLICIT_SEPARATORS = [
    r"\.\s+(?:then|also|next|after that|finally|lastly)\s+",
    r"\s+(?:and also|and then|, then|; also)\s+",
]


def split_requests(prompt: str) -> list[str]:
    """Split a prompt into individual requests."""
    lines = prompt.strip().split('\n')
    requests = []
    current_request = []
    has_delimiters = False

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        is_delimiter_line = any(re.match(p, line_stripped, re.IGNORECASE) for p in EXPLICIT_DELIMITERS)

        if is_delimiter_line:
            has_delimiters = True
            if current_request:
                requests.append(' '.join(current_request))
            cleaned = line_stripped
            for p in EXPLICIT_DELIMITERS:
                cleaned = re.sub(p, '', cleaned, count=1, flags=re.IGNORECASE)
            current_request = [cleaned.strip()]
        else:
            current_request.append(line_stripped)

    if current_request:
        requests.append(' '.join(current_request))

    if has_delimiters and len(requests) > 1:
        return [r for r in requests if r.strip()]

    full_text = ' '.join(lines)
    for sep_pattern in IMPLICIT_SEPARATORS:
        parts = re.split(sep_pattern, full_text, flags=re.IGNORECASE)
        if len(parts) > 1:
            return [p.strip() for p in parts if p.strip()]

    return [prompt.strip()]


def classify_single(prompt: str) -> str:
    """Classify a single request."""
    prompt_lower = prompt.lower().strip()

    if re.search(r"\bsubagent:\s", prompt_lower):
        return "CODING_TASK"

    for pattern in CODING_PATTERNS:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            return "CODING_TASK"

    for pattern in QUICK_PATTERNS:
        if re.search(pattern, prompt_lower, re.IGNORECASE):
            return "QUICK_QUESTION"

    return "QUICK_QUESTION"


def classify_prompt(prompt: str) -> tuple[str, list[tuple[str, str]]]:
    """Classify a prompt, handling multi-request prompts."""
    requests = split_requests(prompt)

    if len(requests) == 1:
        task_type = classify_single(requests[0])
        return task_type, [(requests[0], task_type)]

    classified = [(req, classify_single(req)) for req in requests]
    has_coding = any(t == "CODING_TASK" for _, t in classified)
    overall = "CODING_TASK" if has_coding else "QUICK_QUESTION"

    return overall, classified


def truncate(text: str, max_len: int = 60) -> str:
    """Truncate text for display."""
    if len(text) <= max_len:
        return text
    return text[:max_len-3] + "..."


def main():
    try:
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"[CLASSIFICATION_ERROR: JSON parse failed - {e}] Use your own judgment.")
            sys.exit(0)

        prompt = input_data.get("prompt", "")

        if not prompt or not prompt.strip():
            print("[CLASSIFICATION_SKIPPED: Empty prompt] Use your own judgment.")
            sys.exit(0)

        overall_type, classified_requests = classify_prompt(prompt)

        # Log the classification
        coding_count = sum(1 for _, t in classified_requests if t == "CODING_TASK")
        quick_count = len(classified_requests) - coding_count
        log_prompt_classification(
            prompt_preview=prompt[:100],
            classification=overall_type,
            is_multi_request=len(classified_requests) > 1,
            request_count=len(classified_requests),
            coding_count=coding_count,
            quick_count=quick_count
        )

        # Build context output
        if len(classified_requests) == 1:
            if overall_type == "CODING_TASK":
                context = "[TASK_TYPE: CODING_TASK] This appears to be a coding task. Consider using the 'coder' subagent for autonomous implementation with test verification."
            else:
                context = "[TASK_TYPE: QUICK_QUESTION] This is a quick question or simple task. Answer directly without spawning subagents."
        else:
            lines = [f"[MULTI_REQUEST: {len(classified_requests)} tasks detected ({coding_count} coding, {quick_count} quick)]"]
            lines.append("Tasks to handle:")

            for i, (req_text, req_type) in enumerate(classified_requests, 1):
                type_label = "CODING" if req_type == "CODING_TASK" else "QUICK"
                lines.append(f"  {i}. [{type_label}] {truncate(req_text)}")

            lines.append("")
            lines.append("Execution guidance:")
            if coding_count > 1:
                lines.append("- PARALLEL: Launch multiple 'coder' subagents in parallel for independent CODING tasks")
            elif coding_count == 1:
                lines.append("- Use 'coder' subagent for the CODING task")
            if quick_count > 0:
                lines.append("- Answer QUICK tasks directly (can be done while agents run in background)")
            if coding_count > 0 and quick_count > 0:
                lines.append("- Consider running CODING tasks in background while answering QUICK tasks")

            context = '\n'.join(lines)

        print(context)
        sys.exit(0)

    except Exception as e:
        error_type = type(e).__name__
        print(f"[CLASSIFICATION_ERROR: {error_type} - {e}] Use your own judgment.")
        sys.exit(0)


if __name__ == "__main__":
    main()
