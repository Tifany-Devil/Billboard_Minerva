"""!
@file tests/test_links_basic.py
@brief Basic tests for link generation utilities.
"""

from services.links import spotify_search_url


def test_spotify_search_url_format():
    """!
    @brief Validates the Spotify search URL format and query contents.
    """
    url = spotify_search_url("Hello", "Adele")
    assert url.startswith("https://open.spotify.com/search/")
    assert "hello" in url.lower()
    assert "adele" in url.lower()
