#!/usr/bin/env python3
"""
Test runner for specific library merge scenarios using pytest framework.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from mock_library import MockDJLibrary
from track import Track
from library_diff import DJLibraryDiff

class TestLibraryScenarios:
    """Test specific library merge scenarios using pytest."""
    
    def test_scenario_1_genre_conflicts(self):
        """Test scenario with genre conflicts."""
        print("=== Test Scenario 1: Genre Conflicts ===")
        
        # ID3 Library (original)
        id3_library = MockDJLibrary("ID3Library", "/music")
        id3_library.add_track("/music/song1.mp3", Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock']
        }))
        id3_library.add_track("/music/song2.mp3", Track("/music/song2.mp3", {
            'title': ['Song 2'],
            'artist': ['Artist 2'],
            'genre': ['Pop']
        }))
        
        # Swinsian Library (updated)
        swinsian_library = MockDJLibrary("SwinsianLibrary", "/music")
        swinsian_library.add_track("/music/song1.mp3", Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock', 'Alternative']  # Added genre
        }))
        swinsian_library.add_track("/music/song2.mp3", Track("/music/song2.mp3", {
            'title': ['Song 2'],
            'artist': ['Artist 2'],
            'genre': ['Jazz']  # Changed genre
        }))
        
        print("ID3 Library:")
        print(id3_library.to_yaml())
        print("\nSwinsian Library:")
        print(swinsian_library.to_yaml())
        
        # Show diff
        print("\nDiff (ID3 vs Swinsian):")
        diff = DJLibraryDiff(id3_library, swinsian_library)
        print(diff)
        
        # Merge
        print("\nMerge (ID3 + Swinsian changes):")
        merged_library = id3_library.merge(swinsian_library)
        print(merged_library.to_yaml())
        
        # Assertions
        assert len(merged_library.tracks) == 2
        assert "/music/song1.mp3" in merged_library.tracks
        assert "/music/song2.mp3" in merged_library.tracks
        
        song1_merged = merged_library.tracks["/music/song1.mp3"]
        song2_merged = merged_library.tracks["/music/song2.mp3"]
        
        assert song1_merged.tags['genre'] == ['Rock', 'Alternative']
        assert song2_merged.tags['genre'] == ['Jazz']
    
    def test_scenario_2_track_additions_removals(self):
        """Test scenario with track additions and removals."""
        print("\n=== Test Scenario 2: Track Additions/Removals ===")
        
        # Original Library
        original_library = MockDJLibrary("ID3Library", "/music")
        original_library.add_track("/music/song1.mp3", Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock']
        }))
        original_library.add_track("/music/song2.mp3", Track("/music/song2.mp3", {
            'title': ['Song 2'],
            'artist': ['Artist 2'],
            'genre': ['Pop']
        }))
        
        # Updated Library
        updated_library = MockDJLibrary("ID3Library", "/music")
        updated_library.add_track("/music/song1.mp3", Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock', 'Alternative']  # Modified
        }))
        updated_library.add_track("/music/song3.mp3", Track("/music/song3.mp3", {
            'title': ['Song 3'],
            'artist': ['Artist 3'],
            'genre': ['Jazz']  # Added
        }))
        # song2 was removed
        
        print("Original Library:")
        print(original_library.to_yaml())
        print("\nUpdated Library:")
        print(updated_library.to_yaml())
        
        # Show diff
        print("\nDiff (Original vs Updated):")
        diff = DJLibraryDiff(original_library, updated_library)
        print(diff)
        
        # Merge
        print("\nMerge (Original + Updated changes):")
        merged_library = original_library.merge(updated_library)
        print(merged_library.to_yaml())
        
        # Assertions
        assert len(merged_library.tracks) == 3
        assert "/music/song1.mp3" in merged_library.tracks
        assert "/music/song2.mp3" in merged_library.tracks
        assert "/music/song3.mp3" in merged_library.tracks
        
        song1_merged = merged_library.tracks["/music/song1.mp3"]
        assert song1_merged.tags['genre'] == ["Rock", "Alternative"]
    
    def test_scenario_3_complex_tag_changes(self):
        """Test scenario with complex tag changes."""
        print("\n=== Test Scenario 3: Complex Tag Changes ===")
        
        # Library A
        library_a = MockDJLibrary("ID3Library", "/music")
        library_a.add_track("/music/song1.mp3", Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock'],
            'year': ['2020'],
            'album': ['Album 1']
        }))
        
        # Library B
        library_b = MockDJLibrary("SwinsianLibrary", "/music")
        library_b.add_track("/music/song1.mp3", Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock', 'Alternative'],  # Added genre
            'year': ['2021'],  # Changed year
            'bpm': ['120']  # Added BPM
            # album was removed
        }))
        
        print("Library A:")
        print(library_a.to_yaml())
        print("\nLibrary B:")
        print(library_b.to_yaml())
        
        # Show diff
        print("\nDiff (A vs B):")
        diff = DJLibraryDiff(library_a, library_b)
        print(diff)
        
        # Merge
        print("\nMerge (A + B changes):")
        merged_library = library_a.merge(library_b)
        print(merged_library.to_yaml())
        
        # Assertions
        assert len(merged_library.tracks) == 1
        assert "/music/song1.mp3" in merged_library.tracks
        
        song1_merged = merged_library.tracks["/music/song1.mp3"]
        assert song1_merged.tags['genre'] == ['Rock', 'Alternative']
        assert song1_merged.tags['year'] == ['2021']
        assert song1_merged.tags['bpm'] == ['120']
        assert 'album' not in song1_merged.tags 