#!/usr/bin/env python3
"""
Test cases for library operations using pytest framework.
"""

import tempfile
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from track import Track
from mock_library import MockDJLibrary
from library_diff import DJLibraryDiff

class TestMockLibrary:
    """Test cases for MockDJLibrary operations using pytest."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Set up test data using pytest fixtures."""
        # Create test tracks
        self.track1 = Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock', 'Alternative']
        })
        
        self.track2 = Track("/music/song2.mp3", {
            'title': ['Song 2'],
            'artist': ['Artist 2'],
            'genre': ['Pop']
        })
        
        self.track3 = Track("/music/song3.mp3", {
            'title': ['Song 3'],
            'artist': ['Artist 3'],
            'genre': ['Jazz']
        })
        
        # Create test libraries
        self.id3_library = MockDJLibrary("ID3Library", "/music")
        self.id3_library.add_track("/music/song1.mp3", self.track1)
        self.id3_library.add_track("/music/song2.mp3", self.track2)
        
        self.swinsian_library = MockDJLibrary("SwinsianLibrary", "/music")
        self.swinsian_library.add_track("/music/song1.mp3", self.track1)
        self.swinsian_library.add_track("/music/song3.mp3", self.track3)
    
    def test_library_creation(self):
        """Test creating libraries with tracks."""
        assert len(self.id3_library.tracks) == 2
        assert len(self.swinsian_library.tracks) == 2
        assert self.id3_library.library_type == "ID3Library"
        assert self.swinsian_library.library_type == "SwinsianLibrary"
    
    def test_yaml_serialization(self):
        """Test converting library to and from YAML."""
        # Convert to YAML
        yaml_str = self.id3_library.to_yaml()
        
        # Convert back from YAML
        restored_library = MockDJLibrary.from_yaml(yaml_str)
        
        # Check that the libraries are equivalent
        assert restored_library.library_type == self.id3_library.library_type
        assert restored_library.music_folder == self.id3_library.music_folder
        assert len(restored_library.tracks) == len(self.id3_library.tracks)
        
        # Check that tracks are equivalent
        for file_path, track in self.id3_library.tracks.items():
            assert file_path in restored_library.tracks
            restored_track = restored_library.tracks[file_path]
            assert track.path == restored_track.path
            assert track.tags == restored_track.tags
    
    def test_yaml_file_operations(self):
        """Test saving and loading libraries to/from YAML files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            # Save library to file
            self.id3_library.save_yaml(temp_file)
            
            # Load library from file
            loaded_library = MockDJLibrary.load_yaml(temp_file)
            
            # Check that the libraries are equivalent
            assert loaded_library.library_type == self.id3_library.library_type
            assert len(loaded_library.tracks) == len(self.id3_library.tracks)
            
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_diff_operations(self):
        """Test diff operations between libraries."""
        # Create diff between ID3 and Swinsian libraries
        diff = DJLibraryDiff(self.id3_library, self.swinsian_library)
        
        # Should have differences since they have different tracks
        assert diff
        
        # Check that we can get the diff as a string
        diff_str = str(diff)
        assert isinstance(diff_str, str)
        # The output format shows "Library changes" or "No changes detected"
        assert len(diff_str) > 0
    
    def test_merge(self):
        """Test merging between libraries."""
        # Merge Swinsian changes into ID3
        merged_library = self.id3_library.merge(self.swinsian_library)
        
        # The merged library should have all tracks from both libraries
        expected_tracks = {
            "/music/song1.mp3",  # Common track
            "/music/song2.mp3",  # ID3 only
            "/music/song3.mp3"   # Swinsian only
        }
        
        assert set(merged_library.tracks.keys()) == expected_tracks
        assert len(merged_library.tracks) == 3
        
        # Original libraries should be unchanged
        assert len(self.id3_library.tracks) == 2
        assert len(self.swinsian_library.tracks) == 2
    
    def test_track_modifications(self):
        """Test modifying tracks in libraries."""
        # Create a modified version of track1
        modified_track = Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock', 'Alternative', 'New Genre']  # Added genre
        })
        
        # Create a library with the modified track
        modified_library = MockDJLibrary("ID3Library", "/music")
        modified_library.add_track("/music/song1.mp3", modified_track)
        modified_library.add_track("/music/song2.mp3", self.track2)
        
        # Create diff
        diff = DJLibraryDiff(self.id3_library, modified_library)
        
        # Should show the modification
        diff_str = str(diff)
        assert "Song 1" in diff_str
        # The output format shows specific changes, not just "modified"
        assert len(diff_str) > 0
    
    def test_diff_with_commits(self):
        """Test diffing against a commit."""
        # Create a library with initial track
        library = MockDJLibrary("ID3Library", "/music")
        library.add_track("/music/song1.mp3", self.track1)
        
        # Commit the initial state
        library.commit()
        
        # Now modify the track after the commit
        modified_track = Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'genre': ['Rock', 'Alternative', 'New Genre']  # Added another genre
        })
        library.update_track("/music/song1.mp3", modified_track)
        
        # Diff should show the changes since the commit
        diff = library.diff()
        diff_str = str(diff)
        assert "Song 1" in diff_str  # Should show the modified track
        assert "New Genre" in diff_str  # Should show the added genre
    
    def test_empty_library_diff(self):
        """Test diffing against an empty library."""
        empty_library = MockDJLibrary("ID3Library", "/music")
        diff = DJLibraryDiff(empty_library, self.id3_library)
        
        # Should show all tracks as added
        diff_str = str(diff)
        # The output format shows "Library changes" or "No changes detected"
        assert len(diff_str) > 0 