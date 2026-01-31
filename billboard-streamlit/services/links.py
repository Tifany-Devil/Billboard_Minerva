# services/links.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Literal
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


ITUNES_SEARCH = "https://itunes.apple.com/search"
ODESLI_API = "https://api.song.link/v1-alpha.1/links?url="

Method = Literal["odesli", "search_fallback"]


@dataclass(frozen=True)
class SpotifyLinkResult:
    url: str
    method: Method


def _build_session() -> requests.Session:
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


def itunes_find_track_url(title: str, artist: str, session: Optional[requests.Session] = None) -> Optional[str]:
    """
    Busca no iTunes e retorna um URL (trackViewUrl) para usar como 'fonte' no Odesli.
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
    """
    Converte um link (ex: iTunes/Apple Music) em links de plataformas.
    Retorna o link do Spotify (se existir).
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
    q = quote(f"{title} {artist}".strip())
    return f"https://open.spotify.com/search/{q}"


def best_spotify_link(title: str, artist: str, session: Optional[requests.Session] = None) -> SpotifyLinkResult:
    """
    Retorna SpotifyLinkResult(url, method).
    Tenta:
      1) iTunes -> Odesli -> Spotify (melhor)
      2) fallback: link de busca do Spotify
    """
    s = session or _build_session()
    try:
        it_url = itunes_find_track_url(title, artist, session=s)
        if it_url:
            sp = odesli_get_spotify_url(it_url, session=s)
            if sp:
                return SpotifyLinkResult(url=sp, method="odesli")
    except Exception:
        # silencioso: cai no fallback
        pass

    return SpotifyLinkResult(url=spotify_search_url(title, artist), method="search_fallback")
