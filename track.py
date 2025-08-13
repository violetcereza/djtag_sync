from deepdiff import DeepDiff, Delta
from colorama import Fore, Style
import os

class Track:
    """
    Represents a music track with file path and associated tags.
    """
    
    def __init__(self, path: str, tags: dict = None):
        """
        Initialize a Track with a file path and optional tags.
        
        Args:
            path (str): The file path to the track
            tags (dict, optional): Dictionary of tags associated with the track
        """
        self.path = path
        self.tags = tags or {}
    
    def __repr__(self):
        return f"Track(path='{self.path}', tags={self.tags})"
    
    def __str__(self):
        title = self.tags.get('title')
        artist = self.tags.get('artist')
        if title and artist:
            return f"{Fore.YELLOW}{artist[0]}{Style.RESET_ALL} - {Fore.BLUE}{title[0]}{Style.RESET_ALL}"
        else:
            return f"{Fore.BLUE}{os.path.basename(self.path)}{Style.RESET_ALL}"
    
    def diff(self, other_track: "Track"):
        return DeepDiff(self.tags, other_track.tags, ignore_order=True, report_repetition=True)
    
    def apply(self, diff):
        """
        Apply a DeepDiff delta to this track's tags.
        
        Args:
            diff (DeepDiff): The diff object from track.diff()
        """
        if diff:
            # Create a Delta from the diff and apply it to self.tags
            delta = Delta(diff)
            self.tags = delta + self.tags