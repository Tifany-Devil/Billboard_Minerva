"""!
@file services/billboard.py
@brief Fetch and parse Billboard Hot 100 charts.

The parser prioritizes JSON-LD extraction for resilience against HTML changes and
falls back to HTML scraping when JSON-LD is unavailable.

All network calls use a retry-capable `requests.Session`.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import json
import re

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BILLBOARD_URL = "https://www.billboard.com/charts/hot-100/{date_str}/"


@dataclass(frozen=True)
class ChartEntry:
    """!
    @brief Represents a single chart entry.

    @param rank Chart position (1..N).
    @param title Track title.
    @param artist Track artist.
    """

    rank: int
    title: str
    artist: str

    def to_dict(self) -> Dict[str, str | int]:
        """!
        @brief Convert the entry into a JSON-serializable dict.
        @return A dict with keys: rank, title, artist.
        """
        return asdict(self)


def _build_session() -> requests.Session:
    """!
    @brief Create a requests session configured with retries and headers.
    @return A configured `requests.Session`.
    """
    s = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7",
        }
    )
    return s


def _clean(x: str) -> str:
    """!
    @brief Normalize whitespace and trim.
    @param x Input string.
    @return Cleaned string.
    """
    return re.sub(r"\s+", " ", (x or "").strip())


def _parse_jsonld_itemlist(obj: dict, limit: int) -> List[ChartEntry]:
    """!
    @brief Extract entries from a JSON-LD ItemList structure.

    Expected format:
    - @type == "ItemList"
    - itemListElement contains ListItem objects with `position` and `item`

    @param obj Parsed JSON-LD object.
    @param limit Maximum number of entries to return.
    @return List of extracted `ChartEntry`.
    """
    entries: List[ChartEntry] = []

    if obj.get("@type") != "ItemList":
        return entries

    items = obj.get("itemListElement")
    if not isinstance(items, list):
        return entries

    for it in items:
        if not isinstance(it, dict) or it.get("@type") != "ListItem":
            continue

        pos = it.get("position")
        item = it.get("item", {})
        if not isinstance(item, dict):
            continue

        title = _clean(item.get("name", ""))
        artist = ""

        by = item.get("byArtist")
        if isinstance(by, dict):
            artist = _clean(by.get("name", ""))
        elif isinstance(by, list) and by and isinstance(by[0], dict):
            artist = _clean(by[0].get("name", ""))

        if not title:
            continue

        try:
            rank = int(pos) if pos else len(entries) + 1
        except Exception:
            rank = len(entries) + 1

        entries.append(ChartEntry(rank=rank, title=title, artist=artist))

        if len(entries) >= limit:
            break

    return entries[:limit]


def _parse_jsonld(soup: BeautifulSoup, limit: int) -> List[ChartEntry]:
    """!
    @brief Extract chart entries via JSON-LD scripts.

    This is the preferred parsing strategy because JSON-LD tends to be more stable
    than HTML layout.

    @param soup Parsed HTML document.
    @param limit Maximum number of entries to return.
    @return List of extracted `ChartEntry`.
    """
    entries: List[ChartEntry] = []

    scripts = soup.select('script[type="application/ld+json"]')
    for sc in scripts:
        raw = (sc.string or "").strip()
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        queue = data if isinstance(data, list) else [data]

        expanded: List[dict] = []
        for obj in queue:
            if isinstance(obj, dict) and isinstance(obj.get("@graph"), list):
                expanded.extend([x for x in obj["@graph"] if isinstance(x, dict)])
        queue.extend(expanded)

        for obj in queue:
            if not isinstance(obj, dict):
                continue

            extracted = _parse_jsonld_itemlist(obj, limit)
            if extracted:
                return extracted

    return entries


def _parse_html_fallback(soup: BeautifulSoup, limit: int) -> List[ChartEntry]:
    """!
    @brief Fallback HTML parser for chart entries.

    This is used only when JSON-LD extraction fails.

    @param soup Parsed HTML document.
    @param limit Maximum number of entries to return.
    @return List of extracted `ChartEntry`.
    """
    entries: List[ChartEntry] = []
    seen = set()

    h3s = soup.select("li.o-chart-results-list__item h3#title-of-a-story")
    for h3 in h3s:
        title = _clean(h3.get_text(" ", strip=True))
        item = h3.find_parent("li", class_="o-chart-results-list__item")
        artist = ""

        if item:
            for sp in item.select("span"):
                txt = _clean(sp.get_text(" ", strip=True))
                if not txt:
                    continue
                if txt.upper() in {"NEW", "RE-ENTRY"}:
                    continue
                if len(txt) >= 2 and not txt.isdigit():
                    artist = txt
                    break

        key = (title.lower(), artist.lower())
        if title and key not in seen:
            seen.add(key)
            entries.append(ChartEntry(rank=len(entries) + 1, title=title, artist=artist))

        if len(entries) >= limit:
            break

    return entries[:limit]


def fetch_hot100(date_str: str, limit: int = 10, session: Optional[requests.Session] = None) -> List[Dict]:
    """!
    @brief Fetch and parse the Billboard Hot 100 for a given chart week.

    @param date_str Chart week in the format `YYYY-MM-DD`.
    @param limit Maximum number of entries to return.
    @param session Optional `requests.Session` to reuse connections/retries.
    @return List of dicts with keys: rank, title, artist.
    """
    if limit <= 0:
        return []

    s = session or _build_session()
    url = BILLBOARD_URL.format(date_str=date_str)

    r = s.get(url, timeout=25)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    entries = _parse_jsonld(soup, limit)
    if not entries:
        entries = _parse_html_fallback(soup, limit)

    return [e.to_dict() for e in entries]
