#!/usr/bin/env python3
"""Unit tests for the round-robin distribution in playlist_generator.py.

These tests run with the standard library only -- no Plex server, no
third-party packages. Fake episodes stand in for Plex episode objects;
only the attributes distribute_episodes_to_weeks() actually reads are
provided: parentIndex, index, title, originallyAvailableAt, addedAt.

Run from the repository root:

    python3 -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playlist_generator import PlaylistGenerator


class FakeEpisode:
    """Minimal stand-in for a Plex episode object."""

    def __init__(self, season, number, title, air_date=None, added=None):
        self.parentIndex = season
        self.index = number
        self.title = title
        self.originallyAvailableAt = air_date
        self.addedAt = added if added is not None else datetime(2020, 1, 1)


class FakePlexConnection:
    """Stand-in for PlexConnection; the generator only needs a truthy .plex."""

    plex = True


def make_episodes(count, first_air_date, title_prefix="E"):
    """Build `count` episodes airing one week apart starting at first_air_date."""
    return [
        FakeEpisode(
            season=1,
            number=i + 1,
            title=f"{title_prefix}{i + 1}",
            air_date=first_air_date + timedelta(days=7 * i),
        )
        for i in range(count)
    ]


def week_titles(result, year, week):
    """Titles in a given year/week, in the order the generator placed them."""
    return [entry["title"] for entry in result[year][week]]


class TestDistributeEpisodesToWeeks(unittest.TestCase):
    def setUp(self):
        self.generator = PlaylistGenerator(FakePlexConnection())

    def test_basic_round_robin(self):
        """Each week gets one episode from every show that still has one."""
        shows = {
            "Show A": make_episodes(3, datetime(2020, 1, 1), "A"),
            "Show B": make_episodes(2, datetime(2020, 1, 2), "B"),
            "Show C": make_episodes(1, datetime(2020, 1, 3), "C"),
        }
        result = self.generator.distribute_episodes_to_weeks(shows)

        self.assertEqual(list(result.keys()), [1])
        self.assertEqual(week_titles(result, 1, 1), ["A1", "B1", "C1"])
        self.assertEqual(week_titles(result, 1, 2), ["A2", "B2"])
        self.assertEqual(week_titles(result, 1, 3), ["A3"])
        self.assertNotIn(4, result[1])

    def test_short_show_drops_out_after_its_last_episode(self):
        """A show with one episode appears in week 1 only."""
        shows = {
            "Short": make_episodes(1, datetime(2020, 1, 1), "S"),
            "Long": make_episodes(3, datetime(2020, 1, 2), "L"),
        }
        result = self.generator.distribute_episodes_to_weeks(shows)

        self.assertEqual(week_titles(result, 1, 1), ["S1", "L1"])
        self.assertEqual(week_titles(result, 1, 2), ["L2"])
        self.assertEqual(week_titles(result, 1, 3), ["L3"])

    def test_week_sorted_by_air_date_not_show_name(self):
        """Within a week, episodes are ordered oldest air date first,
        even when that disagrees with alphabetical show order."""
        shows = {
            "Alpha": [FakeEpisode(1, 1, "Alpha E1", datetime(2020, 1, 5))],
            "Mango": [FakeEpisode(1, 1, "Mango E1", datetime(2020, 1, 3))],
            "Zebra": [FakeEpisode(1, 1, "Zebra E1", datetime(2020, 1, 1))],
        }
        result = self.generator.distribute_episodes_to_weeks(shows)

        self.assertEqual(
            week_titles(result, 1, 1), ["Zebra E1", "Mango E1", "Alpha E1"]
        )

    def test_year_rollover(self):
        """After weeks_per_year weeks, distribution continues in a new year."""
        shows = {"Solo": make_episodes(5, datetime(2020, 1, 1), "S")}
        result = self.generator.distribute_episodes_to_weeks(shows, weeks_per_year=2)

        self.assertEqual(sorted(result.keys()), [1, 2, 3])
        self.assertEqual(week_titles(result, 1, 1), ["S1"])
        self.assertEqual(week_titles(result, 1, 2), ["S2"])
        self.assertEqual(week_titles(result, 2, 1), ["S3"])
        self.assertEqual(week_titles(result, 2, 2), ["S4"])
        self.assertEqual(week_titles(result, 3, 1), ["S5"])

    def test_missing_air_date_falls_back_to_added_at(self):
        """An episode with no air date is ordered by its added date."""
        shows = {
            "NoAir": [
                FakeEpisode(1, 1, "NoAir E1", air_date=None,
                            added=datetime(2020, 1, 10))
            ],
            "HasAir": [FakeEpisode(1, 1, "HasAir E1", datetime(2020, 1, 5))],
        }
        result = self.generator.distribute_episodes_to_weeks(shows)

        self.assertEqual(week_titles(result, 1, 1), ["HasAir E1", "NoAir E1"])

    def test_empty_input_returns_empty_result(self):
        self.assertEqual(self.generator.distribute_episodes_to_weeks({}), {})

    def test_single_show_gets_one_episode_per_week(self):
        shows = {"Only": make_episodes(3, datetime(2020, 1, 1), "O")}
        result = self.generator.distribute_episodes_to_weeks(shows)

        self.assertEqual(week_titles(result, 1, 1), ["O1"])
        self.assertEqual(week_titles(result, 1, 2), ["O2"])
        self.assertEqual(week_titles(result, 1, 3), ["O3"])

    def test_entry_shape_carries_show_season_and_episode_number(self):
        shows = {"Show A": make_episodes(1, datetime(2020, 1, 1), "A")}
        result = self.generator.distribute_episodes_to_weeks(shows)

        entry = result[1][1][0]
        self.assertEqual(entry["show"], "Show A")
        self.assertEqual(entry["season"], 1)
        self.assertEqual(entry["episode_num"], 1)
        self.assertEqual(entry["title"], "A1")
        self.assertIs(entry["episode"], shows["Show A"][0])


if __name__ == "__main__":
    unittest.main()
