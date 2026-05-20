"""USCodeLoader — addressable USC corpus backed by nickvido/us-code.

Builds an in-memory index at initialize() time:
    {(title: int, section: str): Path}

Resolution chain:
    1. Parse citation via statute_citation.parse_single
    2. Look up (title, section) in index → repo-relative path
    3. If as_of is None: read current file from working tree
    4. If as_of is set: find the OLRC annual/YYYY tag <= as_of,
       use `git show <tag>:<path>` to get historical text
    5. Extract the specific section block (between this §-header
       and the next §-header) from the chapter file
    6. Build LegalText with corpus_id="us-code", source_commit set
       to the resolved tag/commit, url pointing at Cornell LII

Index build:
    Walk uscode/title-NN-*/chapter-NNN-*.md
    Scan every `## § NNN.` (and `### § NNN.`) header and index
    (title_num, section_num) -> chapter_file_path.

Failure modes (all graceful, never raise out of public methods):
    - Submodule not initialized → initialize() returns {} with warning
    - Citation parses but (title, section) not in index → resolve returns None
    - as_of before earliest tag → resolve to earliest tag, note in result
    - git binary missing → fall back to working-tree-only mode, log warning
"""

from __future__ import annotations

import logging
import re
import subprocess
from datetime import date
from functools import lru_cache
from pathlib import Path

from .corpus_base import CorpusLoader, LegalText
from .statute_citation import parse_single

logger = logging.getLogger(__name__)


# Match `## § 10152.`, `### § 10152.`, etc. Captures the section number
# (digits + optional trailing letter, e.g. "10152" or "1395dd").
_SECTION_HEADER_RE = re.compile(
    r"^(?P<hashes>#{1,3})\s*§\s*(?P<section>\d+[a-z]*)\.\s",
    re.MULTILINE | re.IGNORECASE,
)

_TITLE_NUM_RE = re.compile(r"^title-(\d+)")


@lru_cache(maxsize=512)
def _git_show_cached(root: str, commit: str, relative_path: str) -> str | None:
    """Module-level cache for `git show commit:path` lookups.

    Lives at module scope (not on USCodeLoader) so the cache key
    doesn't include `self` — that's the B019 issue: a method-level
    lru_cache holds a reference to the instance forever.
    """
    try:
        r = subprocess.run(
            ["git", "-C", root, "show", f"{commit}:{relative_path}"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    return r.stdout


class USCodeLoader(CorpusLoader):
    corpus_id = "us-code"

    def __init__(self, submodule_path: Path | str):
        self._root = Path(submodule_path)
        self._uscode_dir = self._root / "uscode"
        # (title, section) -> chapter file path
        self._index: dict[tuple[int, str], Path] = {}
        # Sorted list of (date, tag_name) for as_of lookup
        self._annual_tags: list[tuple[date, str]] = []
        self._initialized = False
        self._git_available = self._check_git()

    # ------------------------------------------------------------------
    # Init + index
    # ------------------------------------------------------------------

    def initialize(self) -> dict[str, int]:
        """Build the (title, section) -> file index. Returns stats."""
        if not self._uscode_dir.exists():
            logger.warning(
                "USC submodule not found at %s; loader disabled. "
                "Run: git submodule update --init --recursive",
                self._uscode_dir,
            )
            return {"titles": 0, "sections_indexed": 0}

        title_dirs = sorted(self._uscode_dir.glob("title-*"))
        sections_indexed = 0
        for title_dir in title_dirs:
            title_num = self._extract_title_num(title_dir.name)
            if title_num is None:
                continue
            for md_file in title_dir.glob("*.md"):
                if md_file.name.startswith("_"):
                    continue  # title metadata files (e.g. _title.md)
                sections_indexed += self._index_file(title_num, md_file)

        if self._git_available:
            self._annual_tags = self._load_annual_tags()

        self._initialized = True
        return {
            "titles": len(title_dirs),
            "sections_indexed": sections_indexed,
            "annual_tags": len(self._annual_tags),
        }

    @staticmethod
    def _extract_title_num(dirname: str) -> int | None:
        """'title-18-crimes-and-criminal-procedure' -> 18."""
        m = _TITLE_NUM_RE.match(dirname)
        return int(m.group(1)) if m else None

    def _index_file(self, title: int, path: Path) -> int:
        """Index every § header in a Markdown chapter file. Returns count indexed."""
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return 0
        count = 0
        for m in _SECTION_HEADER_RE.finditer(text):
            section = m.group("section")
            # First occurrence wins (handles repeated/transferred sections).
            self._index.setdefault((title, section), path)
            count += 1
        return count

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve_citation(
        self,
        citation: str,
        as_of: date | None = None,
    ) -> LegalText | None:
        if not self._initialized:
            return None
        parsed = parse_single(citation)
        if parsed is None:
            return None
        key = (parsed.title, parsed.section)
        path = self._index.get(key)
        if path is None:
            return None

        relative_path = path.relative_to(self._root).as_posix()
        notes: str | None = None

        if as_of is None:
            text, section_title = self._extract_section_from_text(
                path.read_text(encoding="utf-8", errors="replace"),
                parsed.section,
            )
            source_commit = None
        else:
            tag = self._find_tag_for_date(as_of)
            if tag is None:
                # Earlier than earliest available tag: return current text
                # with a note.
                text, section_title = self._extract_section_from_text(
                    path.read_text(encoding="utf-8", errors="replace"),
                    parsed.section,
                )
                source_commit = None
                notes = (
                    f"as_of {as_of.isoformat()} predates earliest available "
                    f"OLRC tag; showing current working-tree text"
                )
            else:
                snapshot = self._read_file_at_commit(relative_path, tag)
                if snapshot is None:
                    text, section_title = self._extract_section_from_text(
                        path.read_text(encoding="utf-8", errors="replace"),
                        parsed.section,
                    )
                    source_commit = None
                    notes = (
                        f"could not retrieve {tag} snapshot; "
                        f"showing current working-tree text"
                    )
                else:
                    text, section_title = self._extract_section_from_text(
                        snapshot, parsed.section
                    )
                    source_commit = tag

        if not text:
            return None

        # Subsection extraction is lossy on this corpus (chapter files use
        # markdown bold for subsections, not nested lists). When a subsection
        # path is requested, we return the full section and note that the
        # caller should narrow visually.
        if parsed.subsection_path:
            notes = (
                (notes + "; " if notes else "")
                + "subsection extraction not supported on this corpus; "
                "returning full section"
            )

        return LegalText(
            corpus_id=self.corpus_id,
            citation=parsed.canonical,
            citation_raw=citation,
            title=section_title or f"§ {parsed.section}",
            text=text,
            source_path=relative_path,
            source_commit=source_commit,
            as_of=as_of,
            url=self._build_external_url(parsed.title, parsed.section),
            notes=notes,
        )

    @staticmethod
    def _extract_section_from_text(full_text: str, section: str) -> tuple[str, str]:
        """Return (section_body, section_title) for a §-section inside a chapter file.

        The body runs from the matching `## § N.` header to the next
        §-header of the same depth (or end-of-file). Returns ("", "") if
        the section header isn't found.
        """
        # Locate this section's header
        header_re = re.compile(
            rf"^(?P<hashes>#{{1,3}})\s*§\s*{re.escape(section)}\.\s+(?P<title>.+)$",
            re.MULTILINE,
        )
        m = header_re.search(full_text)
        if not m:
            return "", ""
        section_title = m.group("title").strip()
        start = m.start()
        same_depth = len(m.group("hashes"))
        # Find the NEXT §-header at the same or shallower depth (i.e.,
        # a sibling section, or a new chapter heading)
        next_pattern = re.compile(
            rf"^(#{{1,{same_depth}}})\s*§\s*\d+[a-z]*\.\s",
            re.MULTILINE,
        )
        next_match = None
        for nm in next_pattern.finditer(full_text, start + 1):
            next_match = nm
            break
        body = full_text[start : next_match.start() if next_match else len(full_text)]
        return body.strip(), section_title

    # ------------------------------------------------------------------
    # External URL
    # ------------------------------------------------------------------

    @staticmethod
    def _build_external_url(title: int, section: str) -> str:
        """Cornell LII canonical URL for a USC section."""
        return f"https://www.law.cornell.edu/uscode/text/{title}/{section}"

    # ------------------------------------------------------------------
    # Git / temporal lookup
    # ------------------------------------------------------------------

    @staticmethod
    def _check_git() -> bool:
        try:
            subprocess.run(
                ["git", "--version"], capture_output=True, timeout=5, check=False
            )
            return True
        except (OSError, subprocess.SubprocessError):
            return False

    def _load_annual_tags(self) -> list[tuple[date, str]]:
        """Return [(year_date, tag_name), ...] sorted ascending.

        Tags look like 'annual/2013', 'annual/2014', etc. We treat each
        as effective on Jan 1 of that year.
        """
        try:
            r = subprocess.run(
                ["git", "-C", str(self._root), "tag", "-l", "annual/*"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return []
        if r.returncode != 0:
            return []
        tags = []
        for line in r.stdout.splitlines():
            line = line.strip()
            m = re.match(r"^annual/(\d{4})$", line)
            if m:
                tags.append((date(int(m.group(1)), 1, 1), line))
        tags.sort()
        return tags

    def _find_tag_for_date(self, as_of: date) -> str | None:
        """Return the annual tag <= as_of, or None if as_of predates all."""
        candidate = None
        for tag_date, tag_name in self._annual_tags:
            if tag_date <= as_of:
                candidate = tag_name
            else:
                break
        return candidate

    def _read_file_at_commit(self, relative_path: str, commit: str) -> str | None:
        """Run `git show commit:relative_path`. Cached at module level
        by (root, commit, path) so historical lookups don't re-shell out."""
        if not self._git_available:
            return None
        return _git_show_cached(str(self._root), commit, relative_path)

    # ------------------------------------------------------------------
    # CorpusLoader interface — remaining methods
    # ------------------------------------------------------------------

    def search_text(self, query: str, limit: int = 10) -> list[LegalText]:
        """Substring search across the indexed chapter files.

        Returns at most `limit` sections whose text contains `query`
        (case-insensitive). Not a real BM25 — adequate for the v3.3.0
        operator-debug use case; a richer search slots in later via a
        rapidfuzz/whoosh layer without changing the public signature.
        """
        if not self._initialized or not query.strip():
            return []
        q_lower = query.lower()
        seen: set[tuple[int, str]] = set()
        results: list[LegalText] = []
        for (title, section), path in self._index.items():
            if len(results) >= limit:
                break
            key = (title, section)
            if key in seen:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if q_lower not in text.lower():
                continue
            seen.add(key)
            citation = f"{title} U.S.C. § {section}"
            hit = self.resolve_citation(citation)
            if hit is not None:
                results.append(hit)
        return results

    def list_amendments(self, citation: str) -> list[dict]:
        """`git log --oneline` for the chapter file containing the cited section.

        Returns [{commit, date, message}, ...]; empty list when git isn't
        available or the citation can't be located.
        """
        if not self._initialized or not self._git_available:
            return []
        parsed = parse_single(citation)
        if parsed is None:
            return []
        path = self._index.get((parsed.title, parsed.section))
        if path is None:
            return []
        relative_path = path.relative_to(self._root).as_posix()
        try:
            r = subprocess.run(
                [
                    "git",
                    "-C",
                    str(self._root),
                    "log",
                    "--pretty=format:%H|%ad|%s",
                    "--date=short",
                    "--",
                    relative_path,
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
                encoding="utf-8",
                errors="replace",
            )
        except (OSError, subprocess.SubprocessError):
            return []
        if r.returncode != 0:
            return []
        out = []
        for line in r.stdout.splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3:
                out.append({"commit": parts[0], "date": parts[1], "message": parts[2]})
        return out

    def statistics(self) -> dict[str, int]:
        return {
            "titles_indexed": len({t for t, _ in self._index.keys()}),
            "sections_indexed": len(self._index),
            "annual_tags": len(self._annual_tags),
        }
