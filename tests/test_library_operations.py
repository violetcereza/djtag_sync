#!/usr/bin/env python3
"""
Simplified test cases for library operations using pytest framework.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from track import Track
from mock_library import MockDJLibrary
from library_diff import DJLibraryDiff

class TestMockLibrary:
    """Simplified test cases for MockDJLibrary operations."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Set up test data."""
        # Create test tracks
        self.track1 = Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock']
        })
        
        self.track2 = Track("/music/song2.mp3", {
            'title': ['Song 2'],
            'artist': ['Artist 2'],
            'genre': ['Pop']
        })
        
        # Create test libraries
        self.id3_library = MockDJLibrary("ID3Library", "/music", {
            "/music/song1.mp3": self.track1,
            "/music/song2.mp3": self.track2
        })
        
        self.swinsian_library = MockDJLibrary("SwinsianLibrary", "/music", {
            "/music/song1.mp3": self.track1,
            "/music/song2.mp3": self.track2
        })
    
    def test_library_creation(self):
        """Test creating libraries."""
        assert len(self.id3_library.tracks) == 2
        assert self.id3_library.library_type == "ID3Library"
    
    def test_diff_operations(self):
        """Test diff operations between libraries."""
        # Create libraries with different shared track
        modified_track = Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Alternative', 'Rock']  # Modified
        })
        
        modified_library = MockDJLibrary("ID3Library", "/music", {
            "/music/song1.mp3": modified_track,
            "/music/song2.mp3": self.track2
        })
        
        diff = DJLibraryDiff(self.id3_library, modified_library)
        assert diff
        assert "Song 1" in str(diff)
    
    def test_empty_library_diff(self):
        """Test diffing against an empty library."""
        empty_library = MockDJLibrary("ID3Library", "/music", {})
        diff = DJLibraryDiff(empty_library, self.id3_library)
        assert "No changes detected" in str(diff)
    
    def test_diff_apply(self):
        """Test applying diffs to a library."""
                # Create libraries with different states
        target_library = MockDJLibrary("ID3Library", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': {'Rock'}
            })
        })
    
        modified_library = MockDJLibrary("ID3Library", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': {'Alternative', 'Rock'},
                'year': ['2021']
            })
        })
        
        # Apply the diff
        diff = DJLibraryDiff(target_library, modified_library)
        target_library.apply(diff)
        
        # Check changes were applied
        track = target_library.tracks["/music/song1.mp3"]
        assert track.tags['genre'] == {'Alternative', 'Rock'}
        assert track.tags['year'] == ['2021']
    
    def test_merge_functionality(self):
        """Test the merge functionality using commits."""
                # Create libraries with shared tracks
        id3_library = MockDJLibrary("ID3Library", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': {'Rock'}
            })
        })
    
        swinsian_library = MockDJLibrary("SwinsianLibrary", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'genre': {'Rock'}
            })
        })
        
        # Commit initial states
        id3_library.commit()
        swinsian_library.commit()
        
        # Modify swinsian library and commit
        modified_track = Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': {'Alternative', 'Rock'}
        })
        swinsian_library.tracks["/music/song1.mp3"] = modified_track
        swinsian_library.commit()
        
        # Merge changes
        id3_library.merge(swinsian_library)
        
        # Check merge worked
        track = id3_library.tracks["/music/song1.mp3"]
        assert track.tags['genre'] == {'Alternative', 'Rock'} 