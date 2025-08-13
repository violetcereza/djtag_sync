#!/usr/bin/env python3
"""
Test to demonstrate the Track-level structural diff and apply fixes.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from track import Track

class TestTrackStructuralDiff:
    """Test that Track.diff() and Track.apply() handle structural differences properly."""
    
    def test_diff_with_structural_differences(self):
        """Test that diff() scaffolds out tag structures for consistent comparison."""
        print("=== Testing Track.diff() with Structural Differences ===")
        
        # Create tracks with different tag structures
        track1 = Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock']
        })
        
        track2 = Track("/music/song1.mp3", {
            'genre': ['Rock', 'Alternative']  # Only genre, no title/artist
        })
        
        print(f"Track1 tags: {track1.tags}")
        print(f"Track2 tags: {track2.tags}")
        
        # Test diff with structural differences
        diff = track1.diff(track2)
        print(f"Diff result: {diff}")
        
        # Should show both genre differences and structural differences
        assert diff is not None
        assert 'Alternative' in str(diff)  # Should detect the new genre
        assert 'title' in str(diff)        # Should detect missing title
        assert 'artist' in str(diff)       # Should detect missing artist
        
        print("✓ Diff correctly detects both content and structural differences")
    
    def test_apply_with_missing_tags(self):
        """Test that apply() pre-scaffolds tags structure to handle missing paths."""
        print("\n=== Testing Track.apply() with Missing Tags ===")
        
        # Create a track with minimal tags
        track = Track("/music/song1.mp3", {
            'genre': ['Rock']
        })
        
        print(f"Initial track tags: {track.tags}")
        
        # Create a diff that would add a new genre
        from deepdiff import DeepDiff
        diff = DeepDiff(
            {'genre': ['Rock']},
            {'genre': ['Rock', 'Alternative']},
            ignore_order=True,
            report_repetition=True
        )
        
        print(f"Diff to apply: {diff}")
        
        # Apply the diff
        track.apply(diff)
        print(f"Track tags after apply: {track.tags}")
        
        # Should have both genres (no alphabetical ordering without library scaffolding)
        assert 'genre' in track.tags
        assert track.tags['genre'] == ['Rock', 'Alternative']  # Order as applied by diff
        
        print("✓ Apply correctly handles missing tag structures")
    
    def test_apply_with_completely_new_tags(self):
        """Test that apply() can add completely new tags that didn't exist before."""
        print("\n=== Testing Track.apply() with Completely New Tags ===")
        
        # Create a track with only genre
        track = Track("/music/song1.mp3", {
            'genre': ['Rock']
        })
        
        print(f"Initial track tags: {track.tags}")
        
        # Create a diff that would add title and artist tags
        from deepdiff import DeepDiff
        diff = DeepDiff(
            {'genre': ['Rock']},
            {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': ['Rock', 'Alternative']
            },
            ignore_order=True,
            report_repetition=True
        )
        
        print(f"Diff to apply: {diff}")
        
        # Apply the diff
        track.apply(diff)
        print(f"Track tags after apply: {track.tags}")
        
        # Should have all tags
        assert 'title' in track.tags
        assert 'artist' in track.tags
        assert 'genre' in track.tags
        assert track.tags['title'] == ['Song 1']
        assert track.tags['artist'] == ['Artist 1']
        assert track.tags['genre'] == ['Rock', 'Alternative']  # Order as applied by diff
        
        print("✓ Apply correctly adds completely new tags")
    
    def test_apply_with_nested_structure_changes(self):
        """Test that apply() handles complex nested structure changes."""
        print("\n=== Testing Track.apply() with Nested Structure Changes ===")
        
        # Create a track with some tags
        track = Track("/music/song1.mp3", {
            'genre': ['Rock'],
            'year': ['2020']
        })
        
        print(f"Initial track tags: {track.tags}")
        
        # Create a diff that modifies existing tags and adds new ones
        from deepdiff import DeepDiff
        diff = DeepDiff(
            {
                'genre': ['Rock'],
                'year': ['2020']
            },
            {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': ['Rock', 'Alternative'],
                'year': ['2021'],
                'bpm': ['120']
            },
            ignore_order=True,
            report_repetition=True
        )
        
        print(f"Diff to apply: {diff}")
        
        # Apply the diff
        track.apply(diff)
        print(f"Track tags after apply: {track.tags}")
        
        # Should have all tags with correct values
        assert track.tags['title'] == ['Song 1']
        assert track.tags['artist'] == ['Artist 1']
        assert track.tags['genre'] == ['Rock', 'Alternative']  # Order as applied by diff
        assert track.tags['year'] == ['2021']
        assert track.tags['bpm'] == ['120']
        
        print("✓ Apply correctly handles complex nested structure changes")
    
    def test_track_simple_diff_and_apply(self):
        """Test that Track.diff() and Track.apply() work without scaffolding."""
        print("\n=== Testing Track Simple Diff and Apply ===")
        
        track1 = Track("/music/song1.mp3", {
            'genre': ['Rock']
        })
        
        track2 = Track("/music/song1.mp3", {
            'genre': ['Rock', 'Alternative']
        })
        
        print(f"Track1 tags: {track1.tags}")
        print(f"Track2 tags: {track2.tags}")
        
        # Test diff
        diff = track1.diff(track2)
        print(f"Diff: {diff}")
        
        # Should detect the genre difference
        assert diff is not None
        assert 'Alternative' in str(diff)
        
        # Test apply
        track1.apply(diff)
        print(f"Track1 tags after apply: {track1.tags}")
        
        # Should have the new genre (no alphabetical ordering without library scaffolding)
        assert track1.tags['genre'] == ['Rock', 'Alternative']  # Order as applied by diff
        
        print("✓ Track diff and apply work correctly without scaffolding")
    
    def test_library_scaffolding_integration(self):
        """Test that library-level scaffolding works correctly."""
        print("\n=== Testing Library-Level Scaffolding ===")
        
        from mock_library import MockDJLibrary
        from track import Track
        
        # Create a mock library that inherits from DJLibrary
        class TestLibrary(MockDJLibrary):
            def _scaffold_track(self, track, diff_obj):
                # Call parent scaffolding to clean up genre tags
                super()._scaffold_track(track, diff_obj)
                
                # Remove all tags except genre (after diff has been applied)
                genre_tags = track.tags.get('genre', [])
                track.tags.clear()
                track.tags['genre'] = genre_tags
        
        # Create libraries with different structures
        library1 = TestLibrary("TestLibrary", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'genre': {'Rock'}
            })
        })
    
        library2 = TestLibrary("TestLibrary", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': {'Rock', 'Alternative'}
            })
        })
        
        print(f"Library1 track tags: {library1.tracks['/music/song1.mp3'].tags}")
        print(f"Library2 track tags: {library2.tracks['/music/song1.mp3'].tags}")
        
        # Create a diff
        from library_diff import DJLibraryDiff
        diff = DJLibraryDiff(library1, library2)
        print(f"Diff: {diff}")
        
        # Apply the diff (should use library scaffolding)
        library1.apply(diff)
        print(f"Library1 track tags after apply: {library1.tracks['/music/song1.mp3'].tags}")
        
        # Should only have genre tags (due to scaffolding)
        track = library1.tracks['/music/song1.mp3']
        assert 'genre' in track.tags
        assert 'title' not in track.tags
        assert 'artist' not in track.tags
        assert track.tags['genre'] == {'Alternative', 'Rock'}  # Library scaffolding provides alphabetical order
        
        print("✓ Library-level scaffolding correctly maintains consistency")
        
        print("\n=== All Track Structural Diff Tests Passed ===") 