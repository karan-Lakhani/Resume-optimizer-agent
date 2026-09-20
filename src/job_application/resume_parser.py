"""
Resume Parser — Milestone 2

Takes a PDF file path, extracts text using PyMuPDF,
sends it to the LLM with strict instructions, and returns
a validated ResumeProfile Pydantic object.

The master resume is NEVER modified after parsing.
"""
from __future__ import annotations

import json
from pathlib import Path

import pymupdf

from src.common.llm_client import LLMEmptyResponseError, call_llm
from src.common.logging import get_logger
from src.common.schemas import ResumeProfile

logger = get_logger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


COLUMN_GAP_RATIO = 0.08  # min horizontal gap between columns, as a fraction of page width


def _detect_column_split(words: list[tuple], page_width: float) -> float | None:
    """
    Look for a single wide horizontal gap that no word crosses — a strong
    signal of a two-column layout (e.g. a sidebar resume template). Returns
    the x-coordinate to split on, or None if the page reads as one column.
    """
    if not words:
        return None

    intervals = sorted((w[0], w[2]) for w in words)
    merged = [intervals[0]]
    for x0, x1 in intervals[1:]:
        if x0 <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], x1))
        else:
            merged.append((x0, x1))

    if len(merged) < 2:
        return None

    gap_size, gap_start = max(
        (merged[i + 1][0] - merged[i][1], merged[i][1]) for i in range(len(merged) - 1)
    )
    if gap_size >= COLUMN_GAP_RATIO * page_width:
        return gap_start + gap_size / 2
    return None


def _render_words(words: list[tuple], uri_links: list[dict]) -> str:
    """
    Reconstruct text from a list of PyMuPDF words, in (block_no, line_no)
    order, appending the URL after any run of words under a link annotation
    (see _extract_page_text for why).
    """
    words_by_line: dict[tuple[int, int], list[tuple[int, str, str | None]]] = {}
    for x0, y0, x1, y1, word, block_no, line_no, word_no in words:
        word_rect = pymupdf.Rect(x0, y0, x1, y1)
        uri = next((link["uri"] for link in uri_links if word_rect.intersects(link["from"])), None)
        words_by_line.setdefault((block_no, line_no), []).append((word_no, word, uri))

    lines = []
    for key in sorted(words_by_line):
        ordered = sorted(words_by_line[key])
        tokens: list[str] = []
        current_uri = None
        for _, word, uri in ordered:
            if current_uri is not None and uri != current_uri:
                tokens.append(f"({current_uri})")
                current_uri = None
            tokens.append(word)
            current_uri = uri
        if current_uri is not None:
            tokens.append(f"({current_uri})")
        lines.append(" ".join(tokens))
    return "\n".join(lines)


def _extract_page_text(page) -> str:
    """
    Reconstruct a page's text, appending the URL after any run of words
    that sits under a URI link annotation.

    Resume PDFs often place a small link/icon glyph next to a project title
    (e.g. a GitHub icon), and the link's clickable rectangle can span the
    whole title, not just the icon. The real URL only exists as a link
    annotation, invisible to plain text extraction — splicing it in by
    position recovers it as ordinary text the LLM can read, while leaving
    the original title words untouched.

    Sorting words by raw (block_no, line_no) assumes reading order follows
    block/line numbering, which holds for single-column resumes but can
    interleave text from side-by-side columns (e.g. a sidebar layout) into
    garbled lines. When a clear column gap is detected, each column is
    extracted and ordered independently (left column fully, then right)
    instead of being merged by raw line position.
    """
    uri_links = [link for link in page.get_links() if link.get("uri")]
    if not uri_links:
        return page.get_text()

    words = page.get_text("words")
    split_x = _detect_column_split(words, page.rect.width)

    if split_x is None:
        return _render_words(words, uri_links)

    left_words = [w for w in words if w[0] < split_x]
    right_words = [w for w in words if w[0] >= split_x]
    return _render_words(left_words, uri_links) + "\n" + _render_words(right_words, uri_links)


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Step 1: Pull raw text out of the PDF, with real URLs spliced in for
    any link-icon glyphs (see _extract_page_text).

    Uses PyMuPDF rather than pdfplumber — pdfplumber's word-gap
    detection drops spaces on some resume PDFs (tightly kerned fonts),
    concatenating words together (e.g. "ChristUniversity"). PyMuPDF
    preserves spacing correctly on the same files.
    """
    logger.info("Extracting text from PDF")

    text = ""
    with pymupdf.open(pdf_path) as pdf:
        for page in pdf:
            page_text = _extract_page_text(page)
            if page_text:
                text += page_text + "\n"

    logger.info("Extracted %d characters from PDF", len(text))
    return text.strip()


MAX_PARSE_ATTEMPTS = 3


def parse_resume_with_llm(raw_text: str) -> dict:
    system_prompt = (PROMPTS_DIR / "resume_parser.txt").read_text()

    prompt = f"""
Parse this resume and return the JSON structure as instructed.

RESUME TEXT:
{raw_text}
"""

    last_error: Exception | None = None
    for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
        logger.info("Sending resume text to LLM for parsing (attempt %d/%d)", attempt, MAX_PARSE_ATTEMPTS)
        try:
            response = call_llm(prompt=prompt, system=system_prompt)

            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])

            parsed = json.loads(cleaned)
            logger.info("LLM returned valid JSON")
            break
        except (json.JSONDecodeError, LLMEmptyResponseError) as e:
            last_error = e
            logger.warning("LLM call unusable on attempt %d/%d: %s", attempt, MAX_PARSE_ATTEMPTS, e)
    else:
        raise last_error
    return parsed


def validate_parsed_resume(parsed_dict: dict) -> ResumeProfile:
    """
    Step 3: Run the LLM output through Pydantic validation.
    If the LLM hallucinated an unexpected structure, Pydantic
    catches it here rather than letting bad data flow downstream.
    """
    logger.info("Validating parsed resume against ResumeProfile schema")
    profile = ResumeProfile(**parsed_dict)
    logger.info("Validation passed")
    return profile


def parse_resume(pdf_path: str) -> ResumeProfile:
    """
    Main entry point — runs the full pipeline:
    PDF → raw text → LLM → JSON → ResumeProfile
    """
    raw_text = extract_text_from_pdf(pdf_path)
    parsed_dict = parse_resume_with_llm(raw_text)
    profile = validate_parsed_resume(parsed_dict)
    return profile