import unicodedata

_QUOTE_CHARS = set("\"'«»“”‘’")
_MIN_NORMALIZED_LEN = 10


def _strip_quote_wrapping(q: str) -> str:
    q = q.strip()
    changed = True
    while changed and q:
        changed = False
        if q[0] in _QUOTE_CHARS:
            q = q[1:].strip()
            changed = True
        if q and q[-1] in _QUOTE_CHARS:
            q = q[:-1].strip()
            changed = True
        if q.startswith("..."):
            q = q[3:].strip()
            changed = True
        if q.startswith("…"):
            q = q[1:].strip()
            changed = True
        if q.endswith("..."):
            q = q[:-3].strip()
            changed = True
        if q.endswith("…"):
            q = q[:-1].strip()
            changed = True
    return q


def _normalize_with_map(s: str) -> tuple[str, list[int]]:
    """Accent-fold + casefold + collapse whitespace.

    Returns ``(normalized, idx_map)`` where ``idx_map[i]`` is the position in
    the original string ``s`` corresponding to ``normalized[i]``.
    """
    out: list[str] = []
    idx_map: list[int] = []
    prev_space = True
    for i, ch in enumerate(s):
        for sub in unicodedata.normalize("NFKD", ch):
            if unicodedata.combining(sub):
                continue
            c = sub.casefold()
            if c.isspace():
                if not prev_space and out:
                    out.append(" ")
                    idx_map.append(i)
                    prev_space = True
            else:
                out.append(c)
                idx_map.append(i)
                prev_space = False
    while out and out[-1] == " ":
        out.pop()
        idx_map.pop()
    return "".join(out), idx_map


def find_quote_offsets(quote: str, section_text: str) -> tuple[int, int] | None:
    """Locate ``quote`` inside ``section_text`` accent- and case-insensitively.

    Returns ``(start, end)`` into the *original* ``section_text``
    (i.e. ``section_text[start:end]`` is the matched region), or ``None`` if
    the quote is absent or too short to be a meaningful citation.
    """
    q = _strip_quote_wrapping(quote)
    norm_q, _ = _normalize_with_map(q)
    if len(norm_q) < _MIN_NORMALIZED_LEN:
        return None

    norm_s, idx_map = _normalize_with_map(section_text)
    pos = norm_s.find(norm_q)
    if pos < 0:
        return None

    start = idx_map[pos]
    end = idx_map[pos + len(norm_q) - 1] + 1
    return start, end


def verify_quotes(
    quotes: list[str], section_text: str
) -> list[tuple[int, int]]:
    """Return verified ``(start, end)`` spans for every quote that is found in
    ``section_text``.  Order and duplicates follow the input list."""
    spans: list[tuple[int, int]] = []
    for q in quotes:
        offsets = find_quote_offsets(q, section_text)
        if offsets is not None:
            spans.append(offsets)
    return spans
