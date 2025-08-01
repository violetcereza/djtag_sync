#!/usr/bin/env python3
"""
DJLibrary base class for music library management.
"""

import os
import pickle
from abc import ABC, abstractmethod
from deepdiff import DeepDiff, Delta
from datetime import datetime

class DJLibrary(ABC):
    """
    Base class for music library management with history tracking.
    """
    
    def __init__(self, music_folder: str):
        """
        Initialize DJLibrary with a music folder path.
        
        Args:
            music_folder (str): Path to the music folder
        """
        self.music_folder = os.path.abspath(os.path.expanduser(music_folder))
        self.library_type = self.__class__.__name__
        self.tracks = self._scan()
        self.last_commit = self._load_last_commit()
    
    @abstractmethod
    def _scan(self):
        """
        Abstract method to scan the library for tracks.
        Must be implemented by subclasses.
        
        Returns:
            dict: Dictionary of {file_path: Track instance}
        """
        pass
    
    @abstractmethod
    def writeLibrary(self):
        """
        Abstract method to write the library to its storage medium.
        Must be implemented by subclasses.
        """
        pass
    
    def _load_last_commit(self):
        """
        Load the last commit from pickle file.
        
        Returns:
            DJLibrary or None: The last committed library state
        """
        try:
            djtag_dir = os.path.join(self.music_folder, '.djtag')
            filename = f"{self.library_type}.pkl"
            filepath = os.path.join(djtag_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            print(f"Error loading last commit for {self.library_type}: {e}")
        return None
    
    def commit(self):
        """
        Commit the current library state to pickle file.
        """
        djtag_dir = os.path.join(self.music_folder, '.djtag', self.library_type)
        os.makedirs(djtag_dir, exist_ok=True)
        filepath = os.path.join(djtag_dir, f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pkl")
        # diff = DeepDiff(self.last_commit.tracks, self.tracks)
        # delta = Delta(diff)
        # print(diff)
        # print(delta)
        # print(len(diff))
        with open(filepath, 'wb') as f:
            pickle.dump(self, f) 