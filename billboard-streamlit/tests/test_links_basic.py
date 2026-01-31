from services.links import spotify_search_url

def test_spotify_search_url_format():
    url = spotify_search_url("Hello", "Adele")
    assert url.startswith("https://open.spotify.com/search/")
    assert "hello" in url.lower()
    assert "adele" in url.lower()
