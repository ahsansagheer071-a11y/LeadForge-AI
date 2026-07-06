import re


def calculate_word_count(text: str) -> int:
    """Split on whitespace, count non-empty tokens."""
    if not text:
        return 0
    return len(text.split())


def estimate_tokens(text: str) -> int:
    """Approximate token count using the common heuristic: len(text) / 4,
    rounded up. This is a rough estimate, not a real tokenizer."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def sanitize_markdown(text: str) -> str:
    """Strip null bytes and control characters, normalize line endings
    to \\n, strip trailing whitespace per line."""
    if not text:
        return ""
    stripped = text.replace("\r\n", "\n").replace("\r", "\n")
    stripped = "".join(ch for ch in stripped if ch >= " " or ch in "\n\t")
    lines = stripped.split("\n")
    lines = [line.rstrip() for line in lines]
    return "\n".join(lines)


def normalize_headings(text: str) -> str:
    """Ensure heading lines (#, ##, ###...) have exactly one space after
    the hash symbols and a blank line before/after each heading."""
    if not text:
        return ""

    lines = text.split("\n")
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        heading_match = re.match(r"^(#{1,6})\s*(.*?)(?:\s+#)*\s*$", line)
        if heading_match:
            hashes = heading_match.group(1)
            content = heading_match.group(2).strip()
            normalized = f"{hashes} {content}" if content else hashes

            has_blank_before = (
                len(result) == 0
                or result[-1] == ""
            )
            if not has_blank_before and result:
                result.append("")

            result.append(normalized)

            has_blank_after = (
                i + 1 >= len(lines)
                or lines[i + 1] == ""
            )
            if not has_blank_after:
                result.append("")
        else:
            result.append(line)
        i += 1
    return "\n".join(result)


def normalize_spacing(text: str) -> str:
    """Collapse 3+ consecutive blank lines into exactly 2, and strip
    leading/trailing blank lines from the document."""
    if not text:
        return ""

    lines = text.split("\n")
    result: list[str] = []
    consecutive_blanks = 0
    for line in lines:
        if line == "":
            consecutive_blanks += 1
            if consecutive_blanks <= 2:
                result.append("")
        else:
            consecutive_blanks = 0
            result.append(line)

    while result and result[0] == "":
        result.pop(0)
    while result and result[-1] == "":
        result.pop()

    return "\n".join(result)


def validate_markdown(text: str) -> bool:
    """Return True if the text is non-empty, has at least one heading,
    and contains no unresolved template placeholders like {{...}} or
    [PLACEHOLDER]. Return False otherwise — do not raise."""
    if not text:
        return False

    if not re.search(r"^#{1,6}\s", text, re.MULTILINE):
        return False

    if re.search(r"\{\{.*?\}\}", text):
        return False

    if re.search(r"\[PLACEHOLDER\]", text, re.IGNORECASE):
        return False

    return True
