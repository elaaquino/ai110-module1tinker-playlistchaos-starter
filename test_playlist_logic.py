"""Tests for playlist_logic, mapped to the desired requirements."""

from playlist_logic import (
    DEFAULT_PROFILE,
    build_playlists,
    classify_song,
    compute_playlist_stats,
    lucky_pick,
    merge_playlists,
    normalize_song,
    random_choice_or_none,
    search_songs,
)


# --- Mood engine -----------------------------------------------------------

def test_hype_by_energy():
    song = {"title": "x", "artist": "a", "genre": "pop", "energy": 9}
    assert classify_song(normalize_song(song), DEFAULT_PROFILE) == "Hype"


def test_hype_by_favorite_genre():
    # rock is the default favorite_genre; energy below the hype threshold.
    song = {"title": "x", "artist": "a", "genre": "rock", "energy": 4}
    assert classify_song(normalize_song(song), DEFAULT_PROFILE) == "Hype"


def test_hype_by_keyword():
    # "party" is a hype keyword, even when it is not the favorite genre.
    profile = dict(DEFAULT_PROFILE, favorite_genre="jazz")
    song = {"title": "x", "artist": "a", "genre": "party", "energy": 2}
    assert classify_song(normalize_song(song), profile) == "Hype"


def test_chill_by_energy():
    profile = dict(DEFAULT_PROFILE, favorite_genre="jazz")
    song = {"title": "x", "artist": "a", "genre": "pop", "energy": 2}
    assert classify_song(normalize_song(song), profile) == "Chill"


def test_chill_by_title_keyword_case_insensitive():
    profile = dict(DEFAULT_PROFILE, favorite_genre="jazz")
    song = {"title": "Deep SLEEP Vibes", "artist": "a", "genre": "pop", "energy": 5}
    assert classify_song(normalize_song(song), profile) == "Chill"


def test_mixed_fallback():
    profile = dict(DEFAULT_PROFILE, favorite_genre="jazz")
    song = {"title": "x", "artist": "a", "genre": "pop", "energy": 5}
    assert classify_song(normalize_song(song), profile) == "Mixed"


# --- Search ----------------------------------------------------------------

def test_search_partial_case_insensitive():
    songs = [normalize_song({"title": "t", "artist": "AC/DC", "genre": "rock", "energy": 9})]
    assert len(search_songs(songs, "ac", field="artist")) == 1
    assert len(search_songs(songs, "AC", field="artist")) == 1
    assert len(search_songs(songs, "dc", field="artist")) == 1


def test_search_no_match():
    songs = [normalize_song({"title": "t", "artist": "Queen", "genre": "rock", "energy": 8})]
    assert search_songs(songs, "zzz", field="artist") == []


def test_search_empty_query_returns_all():
    songs = [normalize_song({"title": "t", "artist": "Queen", "genre": "rock", "energy": 8})]
    assert search_songs(songs, "") == songs


# --- Stats -----------------------------------------------------------------

def test_stats_totals_and_averages():
    playlists = {
        "Hype": [{"artist": "a", "energy": 10}, {"artist": "b", "energy": 8}],
        "Chill": [{"artist": "c", "energy": 2}],
        "Mixed": [{"artist": "d", "energy": 5}],
    }
    stats = compute_playlist_stats(playlists)
    assert stats["total_songs"] == 4
    assert stats["hype_count"] == 2
    assert stats["hype_ratio"] == 0.5
    # (10 + 8 + 2 + 5) / 4 == 6.25
    assert stats["avg_energy"] == 6.25


def test_stats_empty():
    stats = compute_playlist_stats({"Hype": [], "Chill": [], "Mixed": []})
    assert stats["total_songs"] == 0
    assert stats["hype_ratio"] == 0.0
    assert stats["avg_energy"] == 0.0


# --- Lucky pick ------------------------------------------------------------

def test_lucky_pick_hype_only():
    playlists = {
        "Hype": [{"title": "H", "artist": "a"}],
        "Chill": [{"title": "C", "artist": "b"}],
        "Mixed": [{"title": "M", "artist": "c"}],
    }
    for _ in range(20):
        assert lucky_pick(playlists, mode="hype")["title"] == "H"


def test_lucky_pick_any_includes_mixed():
    playlists = {"Hype": [], "Chill": [], "Mixed": [{"title": "M", "artist": "c"}]}
    assert lucky_pick(playlists, mode="any")["title"] == "M"


def test_lucky_pick_empty_returns_none():
    assert lucky_pick({"Hype": [], "Chill": [], "Mixed": []}, mode="hype") is None
    assert random_choice_or_none([]) is None


# --- Normalization ---------------------------------------------------------

def test_normalize_trims_and_lowercases():
    song = normalize_song(
        {"title": "  My Song  ", "artist": "  The Band  ", "genre": " ROCK ", "energy": "7"}
    )
    assert song["title"] == "My Song"
    assert song["artist"] == "the band"
    assert song["genre"] == "rock"
    assert song["energy"] == 7


def test_normalize_tags_string_to_list():
    song = normalize_song({"title": "t", "artist": "a", "genre": "rock", "tags": "solo"})
    assert song["tags"] == ["solo"]


# --- Merge does not mutate inputs -----------------------------------------

def test_merge_does_not_mutate_inputs():
    a = {"Hype": [{"title": "H"}]}
    b = {"Hype": [{"title": "H2"}]}
    merged = merge_playlists(a, b)
    assert len(merged["Hype"]) == 2
    assert len(a["Hype"]) == 1  # original untouched


def test_build_playlists_assigns_mood():
    songs = [{"title": "t", "artist": "a", "genre": "rock", "energy": 9}]
    playlists = build_playlists(songs, DEFAULT_PROFILE)
    assert playlists["Hype"][0]["mood"] == "Hype"