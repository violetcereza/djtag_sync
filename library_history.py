#!/usr/bin/env python3
"""
LibraryHistory class for managing library instances and their history.
"""

from typing import Union
from swinsian import SwinsianLibrary
from id3 import ID3Library

class LibraryHistory:
    """
    A class that holds a library instance and provides history/commit functionality.
    """
    
    def __init__(self, library: Union[SwinsianLibrary, ID3Library]):
        """
        Initialize LibraryHistory with a library instance.
        
        Args:
            library: Either a SwinsianLibrary or ID3Library instance
        """
        if not isinstance(library, (SwinsianLibrary, ID3Library)):
            raise TypeError("library must be either SwinsianLibrary or ID3Library")
        
        self.library = library
        self.library_type = type(library).__name__
    
    def commit(self):
        """
        Commit changes to the library.
        This is an empty method that can be overridden or extended.
        """
        pass
    
