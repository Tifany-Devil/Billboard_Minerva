"""!
@file services/links.py
@brief Utilities to generate Spotify links without using the Spotify API.

This module attempts to resolve a direct Spotify URL using a best-effort strategy:
1) iTunes Search -> obtain a track URL
2) Odesli (song.link) -> convert to platform links and pick Spotify
3) Fallback to a Spotify Search URL

All network calls use a retry-capable `requests.Session`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


ITUNES_SEARCH = "https://itunes.apple.com/search"
ODESLI_API = "https://api.song.link/v1-alpha.1/links?url="

Method = Literal["odesli", "search_fallback"]


@dataclass(frozen=True)
class SpotifyLinkResult:
    """!
    @brief Result of Spotify link resolution.

    @param url Resolved Spotify URL (direct or search).
    @param method Resolution method used.
    """

    url: str
    method: Method


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
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    return s


def itunes_find_track_url(
    title: str, artist: str, session: Optional[requests.Session] = None
) -> Optional[str]:
    """!
    @brief Search iTunes for a track and return its `trackViewUrl`.

    The returned URL is typically used as the input for Odesli conversion.

    @param title Track title.
    @param artist Track artist.
    @param session Optional `requests.Session` to reuse connections/retries.
    @return A track URL if found, otherwise `None`.
    """
    term = f"{title} {artist}".strip()
    if not term:
        return None

    s = session or _build_session()
    params = {
        "term": term,
        "media": "music",
        "entity": "song",
        "limit": 1,
        "country": "US",
    }
    r = s.get(ITUNES_SEARCH, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    results = data.get("results", [])
    if not results:
        return None
    return results[0].get("trackViewUrl")


def odesli_get_spotify_url(source_url: str, session: Optional[requests.Session] = None) -> Optional[str]:
    """!
    @brief Convert a source URL (e.g., iTunes) into a Spotify URL using Odesli.

    @param source_url Source track URL to convert.
    @param session Optional `requests.Session` to reuse connections/retries.
    @return Spotify URL if available, otherwise `None`.
    """
    if not source_url:
        return None

    s = session or _build_session()
    r = s.get(ODESLI_API + quote(source_url, safe=""), timeout=20)
    r.raise_for_status()
    data = r.json()

    links = data.get("linksByPlatform", {}) or {}
    sp = links.get("spotify")
    if isinstance(sp, dict):
        return sp.get("url")
    return None


def spotify_search_url(title: str, artist: str) -> str:
    """!
    @brief Build a Spotify search URL for the given title and artist.

    @param title Track title.
    @param artist Track artist.
    @return Spotify search URL.
    """
    q = quote(f"{title} {artist}".strip())
    return f"https://open.spotify.com/search/{q}"


def best_spotify_link(title: str, artist: str, session: Optional[requests.Session] = None) -> SpotifyLinkResult:
    """!
    @brief Resolve the best Spotify link for a track without using Spotify APIs.

    Strategy:
    - Try: iTunes -> Odesli -> Spotify (preferred)
    - Fallback: Spotify search URL

    @param title Track title.
    @param artist Track artist.
    @param session Optional `requests.Session` to reuse connections/retries.
    @return A `SpotifyLinkResult` containing the URL and the resolution method.
    """
    s = session or _build_session()
    try:
        it_url = itunes_find_track_url(title, artist, session=s)
        if it_url:
            sp = odesli_get_spotify_url(it_url, session=s)
            if sp:
                return SpotifyLinkResult(url=sp, method="odesli")
    except Exception:
        pass

    return SpotifyLinkResult(url=spotify_search_url(title, artist), method="search_fallback")
