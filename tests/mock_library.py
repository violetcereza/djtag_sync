#!/usr/bin/env python3
"""
Mock DJLibrary for testing - represents libraries as YAML and runs simulated operations.
"""

import yaml
from typing import Dict, Any, Optional
from track import Track
from library_diff import DJLibraryDiff

class MockDJLibrary:
    """
    A mock DJLibrary that can be represented as YAML and run simulated operations.
    """
    
    def __init__(self, library_type: str, music_folder: str = "/mock/music", tracks: Optional[Dict[str, Track]] = None):
        """
        Initialize a mock library.
        
        Args:
            library_type (str): Type of library (e.g., 'ID3Library', 'SwinsianLibrary')
            music_folder (str): Mock music folder path
            tracks (dict, optional): Dictionary of {file_path: Track} instances
        """
        self.library_type = library_type
        self.music_folder = music_folder
        self.tracks = tracks or {}
        self.commits = []  # List of commit timestamps
        self.commit_libraries = {}  # Dict of {timestamp: library_instance}
        self.meta = {}
    
    def add_track(self, file_path: str, track: Track):
        """Add a track to the library."""
        self.tracks[file_path] = track
    
    def remove_track(self, file_path: str):
        """Remove a track from the library."""
        if file_path in self.tracks:
            del self.tracks[file_path]
    
    def update_track(self, file_path: str, track: Track):
        """Update a track in the library."""
        self.tracks[file_path] = track
    
    def to_yaml(self) -> str:
        """
        Convert the library to YAML representation.
        
        Returns:
            str: YAML string representation of the library
        """
        library_data = {
            'library_type': self.library_type,
            'music_folder': self.music_folder,
            'tracks': {}
        }
        
        for file_path, track in self.tracks.items():
            library_data['tracks'][file_path] = {
                'path': track.path,
                'tags': track.tags
            }
        
        return yaml.dump(library_data, default_flow_style=False, sort_keys=False)
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'MockDJLibrary':
        """
        Create a MockDJLibrary from YAML string.
        
        Args:
            yaml_str (str): YAML string representation
            
        Returns:
            MockDJLibrary: Library instance
        """
        data = yaml.safe_load(yaml_str)
        
        library = cls(
            library_type=data['library_type'],
            music_folder=data['music_folder']
        )
        
        for file_path, track_data in data['tracks'].items():
            track = Track(track_data['path'], track_data['tags'])
            library.tracks[file_path] = track
        
        return library
    
    def save_yaml(self, file_path: str):
        """Save the library to a YAML file."""
        with open(file_path, 'w') as f:
            f.write(self.to_yaml())
    
    @classmethod
    def load_yaml(cls, file_path: str) -> 'MockDJLibrary':
        """Load a library from a YAML file."""
        with open(file_path, 'r') as f:
            return cls.from_yaml(f.read())
    
    def load_commit(self, commit_datetime):
        """
        Load the commit from the commit_libraries dict.
        """
        if commit_datetime not in self.commit_libraries:
            raise ValueError(f"Commit {commit_datetime} not found")
        return self.commit_libraries[commit_datetime]
    
    def commit(self):
        """
        Commit the current library state.
        For MockDJLibrary, this adds the current state to the commits list.
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
    
    def diff(self) -> DJLibraryDiff:
        """
        Diff the current library state with the most recent commit.
        Follows the same convention as DJLibrary.
        """
        if not self.commits:
            raise ValueError("No commits found to diff against.")
        most_recent_commit = max(self.commits)
        commit = self.load_commit(most_recent_commit)
        diff = DJLibraryDiff(commit, self)
        return diff
    
    def merge(self, other_library: 'MockDJLibrary') -> 'MockDJLibrary':
        """
        Merge with another library without modifying the original.
        Follows the same convention as DJLibrary.
        
        Args:
            other_library (MockDJLibrary): Library to merge from
            
        Returns:
            MockDJLibrary: New library with merged changes
        """
        # Create a copy of this library
        merged_library = MockDJLibrary(
            library_type=self.library_type,
            music_folder=self.music_folder,
            tracks=self.tracks.copy()
        )
        
        # Apply all tracks from the other library (this simulates a merge)
        for file_path, track in other_library.tracks.items():
            merged_library.tracks[file_path] = track
        
        return merged_library
    
    def __str__(self):
        """String representation of the library."""
        return f"{self.library_type}({len(self.tracks)} tracks)"
    
    def __repr__(self):
        """Detailed string representation."""
        return f"MockDJLibrary(type={self.library_type}, tracks={len(self.tracks)})" 