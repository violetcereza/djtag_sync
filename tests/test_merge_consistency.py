#!/usr/bin/env python3
"""
Test to demonstrate the merge consistency fix.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from track import Track
from mock_library import MockDJLibrary
from library_diff import DJLibraryDiff

class TestMergeConsistency:
    """Test that merge operations maintain consistent tag structures."""
    
    def test_merge_consistency_fix(self):
        """Test that merge only applies relevant tags to prevent inconsistent states."""
        print("=== Testing Merge Consistency Fix ===")
        
                # Create ID3 library with full tag structure (like real ID3 files)
        id3_library = MockDJLibrary("ID3Library", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'title': ['Song 1'],
                'artist': ['Artist 1'],
                'album': ['Album 1'],
                'genre': {'Rock'}
            })
        })
    
        # Create Swinsian library with only genre tags (like real Swinsian DB)
        swinsian_library = MockDJLibrary("SwinsianLibrary", "/music", {
            "/music/song1.mp3": Track("/music/song1.mp3", {
                'genre': {'Rock'}
            })
        })
        
        # Commit initial states
        id3_library.commit()
        swinsian_library.commit()
        
        print(f"Initial ID3 track tags: {id3_library.tracks['/music/song1.mp3'].tags}")
        print(f"Initial Swinsian track tags: {swinsian_library.tracks['/music/song1.mp3'].tags}")
        
        # Modify ID3 library to add a new genre
        modified_track = Track("/music/song1.mp3", {
            'title': ['Song 1'],
            'artist': ['Artist 1'],
            'album': ['Album 1'],
            'genre': {'Alternative', 'Rock'}  # Added 'Alternative'
        })
        id3_library.tracks["/music/song1.mp3"] = modified_track
        id3_library.commit()
        
        print(f"Modified ID3 track tags: {id3_library.tracks['/music/song1.mp3'].tags}")
        
        # Merge ID3 changes into Swinsian
        print("\n--- Merging ID3 changes into Swinsian ---")
        swinsian_library.merge(id3_library)
        
        print(f"Swinsian track tags after merge: {swinsian_library.tracks['/music/song1.mp3'].tags}")
        
        # Verify that Swinsian only has genre tags (no title/artist/album)
        swinsian_track = swinsian_library.tracks["/music/song1.mp3"]
        assert 'genre' in swinsian_track.tags
        assert 'title' not in swinsian_track.tags  # Should not have title
        assert 'artist' not in swinsian_track.tags  # Should not have artist
        assert 'album' not in swinsian_track.tags   # Should not have album
        assert swinsian_track.tags['genre'] == {'Alternative', 'Rock'}  # Should have new genre
        
        print("✓ Swinsian library only contains genre tags (consistent with its structure)")
        
        # Now test the reverse: merge Swinsian changes into ID3
        print("\n--- Merging Swinsian changes into ID3 ---")
        
        # Modify Swinsian library
        swinsian_modified = Track("/music/song1.mp3", {
            'genre': ['Alternative', 'Rock', 'Jazz']  # Added 'Jazz'
        })
        swinsian_library.tracks["/music/song1.mp3"] = swinsian_modified
        swinsian_library.commit()
        
        # Merge Swinsian changes into ID3
        id3_library.merge(swinsian_library)
        
        print(f"ID3 track tags after merge: {id3_library.tracks['/music/song1.mp3'].tags}")
        
        # Verify that ID3 maintains its full tag structure but gets genre updates
        id3_track = id3_library.tracks["/music/song1.mp3"]
        assert 'title' in id3_track.tags  # Should still have title
        assert 'artist' in id3_track.tags  # Should still have artist
        assert 'album' in id3_track.tags   # Should still have album
        assert 'genre' in id3_track.tags   # Should have genre
        assert id3_track.tags['genre'] == {'Alternative', 'Jazz', 'Rock'}  # Should have all genres
        
        print("✓ ID3 library maintains full tag structure with updated genres")
        
        print("\n=== Merge Consistency Fix Test Passed ===") 