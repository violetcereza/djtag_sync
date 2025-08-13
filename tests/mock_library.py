#!/usr/bin/env python3
"""
Mock DJLibrary for testing - runs simulated operations without filesystem interaction.
"""

from typing import Dict, Any, Optional
from track import Track
from library_diff import DJLibraryDiff
from library import DJLibrary

class MockDJLibrary(DJLibrary):
    """
    A mock DJLibrary that runs simulated operations without filesystem interaction.
    """
    
    def __init__(self, library_type: str, music_folder: str = "/mock/music", tracks: Optional[Dict[str, Track]] = None):
        """
        Initialize a mock library.
        
        Args:
            library_type (str): Type of library (e.g., 'ID3Library', 'SwinsianLibrary')
            music_folder (str): Mock music folder path
            tracks (dict, optional): Dictionary of {file_path: Track} instances
        """
        # Set tracks before calling parent constructor
        self._tracks = tracks or {}
        
        # Call parent constructor
        super().__init__(music_folder)
        
        # Override library_type
        self.library_type = library_type
        
        # Mock-specific attributes
        self.commit_libraries = {}  # Dict of {timestamp: library_instance}
    
    def _scan(self):
        """
        Mock scan - returns the tracks that were set in the constructor.
        """
        return self._tracks
    
    def writeLibrary(self):
        """
        Mock write - does nothing since this is for testing.
        """
        pass
    
    def _scan_commits(self):
        """
        Mock scan commits - returns empty list since this is for testing.
        """
        return []
    
    def _write_meta(self):
        """
        Mock write meta - does nothing since this is for testing.
        """
        pass
    
    def load_commit(self, commit_datetime):
        """
        Load the commit from the commit_libraries dict.
        Override parent method to use in-memory storage.
        """
        if commit_datetime is None:
            # Return an empty library for None datetime
            return MockDJLibrary(self.library_type, self.music_folder, {})
        if commit_datetime not in self.commit_libraries:
            raise ValueError(f"Commit {commit_datetime} not found")
        return self.commit_libraries[commit_datetime]
    
    def commit(self):
        """
        Commit the current library state.
        Override parent method to use in-memory storage.
        """
        from datetime import datetime
        
        # Create a deep copy of the current state
        commit_tracks = {}
        for file_path, track in self.tracks.items():
            # Create a new Track instance with the same data
            commit_track = Track(track.path, track.tags.copy())
            commit_tracks[file_path] = commit_track
        
        commit_library = MockDJLibrary(
            self.library_type,
            self.music_folder,
            commit_tracks
        )
        
        # Add to commits
        timestamp = datetime.now()
        self.commits.append(timestamp)
        self.commit_libraries[timestamp] = commit_library
    