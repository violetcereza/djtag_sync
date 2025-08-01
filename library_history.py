#!/usr/bin/env python3
"""
LibraryHistory class for managing library instances and their history.
"""

from typing import Union
from swinsian import SwinsianLibrary
from id3 import ID3Library
import os
import pickle

class LibraryHistory:
    """
    A class that holds a library instance and provides history/commit functionality.
    """
    
    def __init__(self, library: Union[SwinsianLibrary, ID3Library], music_folder: str):
        """
        Initialize LibraryHistory with a library instance.
        
        Args:
            library: Either a SwinsianLibrary or ID3Library instance
        """
        if not isinstance(library, (SwinsianLibrary, ID3Library)):
            raise TypeError("library must be either SwinsianLibrary or ID3Library")
        
        self.library = library
        self.library_type = type(library).__name__ 
        self.last_commit = None
        try:
            if music_folder:
                djtag_dir = os.path.join(os.path.abspath(os.path.expanduser(music_folder)), '.djtag')
                filename = f"{self.library_type}.pkl"
                filepath = os.path.join(djtag_dir, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        self.last_commit = pickle.load(f)
        except Exception as e:
            print(f"Error loading last commit for {self.library_type}: {e}")
            self.last_commit = None
    
    def commit(self, music_folder: str):
        """
        Commit changes to the library.
        This is an empty method that can be overridden or extended.
        """

        djtag_dir = os.path.join(os.path.abspath(os.path.expanduser(music_folder)), '.djtag')
        os.makedirs(djtag_dir, exist_ok=True)
        filename = f"{self.library_type}.pkl"
        filepath = os.path.join(djtag_dir, filename)
        with open(filepath, 'wb') as f:
            pickle.dump(self.library, f)
    
