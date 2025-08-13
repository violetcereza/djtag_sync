#!/usr/bin/env python3
"""
Simplified scenario tests for library operations.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from track import Track
from mock_library import MockDJLibrary
from library_diff import DJLibraryDiff

class TestLibraryScenarios:
    """Simplified scenario tests for library operations."""
    
    def test_comprehensive_scenarios(self):
        """Test comprehensive scenarios covering main functionality."""
        print("=== Comprehensive Library Scenarios ===")
        
        # Scenario 1: Basic genre changes
        print("\n--- Scenario 1: Genre Changes ---")
        id3_library = MockDJLibrary("ID3Library", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': ['Rock']
            })
        })
        
        swinsian_library = MockDJLibrary("SwinsianLibrary", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': ['Rock']
            })
        })
        
        # Commit initial states
        id3_library.commit()
        swinsian_library.commit()
        
        # Modify swinsian library
        modified_track = Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Alternative', 'Rock']
        })
        swinsian_library.tracks["/music/song1.mp3"] = modified_track
        swinsian_library.commit()
        
        # Merge changes
        id3_library.merge(swinsian_library)
        
        # Verify changes
        track = id3_library.tracks["/music/song1.mp3"]
        assert track.tags['genre'] == ['Alternative', 'Rock']
        print(f"✓ Genre change applied: {track.tags['genre']}")
        
        # Scenario 2: Complex tag changes
        print("\n--- Scenario 2: Complex Tag Changes ---")
        library_a = MockDJLibrary("ID3Library", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': ['Rock'],
                'year': ['2020']
            })
        })
        
        library_b = MockDJLibrary("SwinsianLibrary", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': ['Rock'],
                'year': ['2020']
            })
        })
        
        # Commit initial states
        library_a.commit()
        library_b.commit()
        
        # Modify library_b with complex changes
        modified_track = Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Alternative', 'Rock'],
            'year': ['2021'],
            'bpm': ['120']
        })
        library_b.tracks["/music/song1.mp3"] = modified_track
        library_b.commit()
        
        # Merge changes
        library_a.merge(library_b)
        
        # Verify complex changes
        track = library_a.tracks["/music/song1.mp3"]
        assert track.tags['genre'] == ['Alternative', 'Rock']
        assert track.tags['year'] == ['2021']
        assert track.tags['bpm'] == ['120']
        print(f"✓ Complex changes applied: genre={track.tags['genre']}, year={track.tags['year']}, bpm={track.tags['bpm']}")
        
        # Scenario 3: Diff behavior with shared tracks
        print("\n--- Scenario 3: Diff Behavior ---")
        shared_library = MockDJLibrary("ID3Library", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': ['Rock']
            })
        })
        
        different_library = MockDJLibrary("SwinsianLibrary", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': ['Alternative', 'Rock']
            }),
            "/music/song2.mp3": Track("/music/song2.mp3", {
                'title': ['Song 2'],
                'artist': ['Artist 2'],
                'genre': ['Pop']
            })
        })
        
        # Diff should only show changes for shared tracks
        diff = DJLibraryDiff(shared_library, different_library)
        diff_str = str(diff)
        assert "Song 1" in diff_str  # Shared track
        assert "Song 2" not in diff_str  # Non-shared track
        print(f"✓ Diff only shows shared tracks: {diff_str}")
        
        print("\n=== All scenarios completed successfully ===") 