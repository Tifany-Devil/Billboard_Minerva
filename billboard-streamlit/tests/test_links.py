"""!
@file tests/test_links.py
@brief Tests for Spotify search URL generation.
"""

from services.links import spotify_search_url


def test_spotify_search_url():
    """!
    @brief Ensures `spotify_search_url` produces a Spotify search URL.
    """
    url = spotify_search_url("Hello", "Adele")
    assert url.startswith("https://open.spotify.com/search/")
    assert "Hello" in url or "hello" in url.lower()
