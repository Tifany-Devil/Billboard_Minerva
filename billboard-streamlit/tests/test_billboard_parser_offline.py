"""!
@file tests/test_billboard_parser_offline.py
@brief Offline tests for Billboard parser behavior.

These tests validate JSON-LD parsing without relying on network access.
"""

import requests

from services.billboard import fetch_hot100


class FakeResponse:
    """!
    @brief Minimal response stub compatible with `requests.Response` usage in the codebase.
    """

    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    """!
    @brief Minimal session stub providing `.get()` for offline parsing tests.
    """

    def __init__(self, html):
        self._html = html

    def get(self, url, timeout=25):
        return FakeResponse(self._html, 200)


def test_fetch_hot100_from_jsonld_offline():
    """!
    @brief Ensures `fetch_hot100` can parse ItemList JSON-LD.
    """
    html = """
    <html><head>
      <script type="application/ld+json">
      {
        "@type": "ItemList",
        "itemListElement": [
          {"@type":"ListItem","position":1,"item":{"name":"Song A","byArtist":{"name":"Artist A"}}},
          {"@type":"ListItem","position":2,"item":{"name":"Song B","byArtist":{"name":"Artist B"}}}
        ]
      }
      </script>
    </head><body></body></html>
    """
    session = FakeSession(html)
    out = fetch_hot100("2022-01-01", limit=2, session=session)

    assert len(out) == 2
    assert out[0]["rank"] == 1
    assert out[0]["title"] == "Song A"
    assert out[0]["artist"] == "Artist A"
