import types
import requests

from services.billboard import fetch_hot100

class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

class FakeSession:
    def __init__(self, html):
        self._html = html
    def get(self, url, timeout=25):
        return FakeResponse(self._html, 200)

def test_fetch_hot100_from_jsonld_offline():
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
