from deepdiff import DeepDiff, Delta

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
        return f"Track: {self.path}"
    
    def add_tag(self, key: str, value: str):
        """Add a tag to the track."""
        self.tags[key] = value
    
    def remove_tag(self, key: str):
        """Remove a tag from the track."""
        if key in self.tags:
            del self.tags[key]
    
    def get_tag(self, key: str, default=None):
        """Get a tag value, returning default if not found."""
        return self.tags.get(key, default)
    
    def diff(self, other: 'Track') -> DeepDiff:
        """
        Compare this track's tags with another track's tags and return the differences.
        
        Args:
            other (Track): Another Track object to compare against
            
        Returns:
            DeepDiff: A DeepDiff object containing the differences between the tracks' tags
        """
        if not isinstance(other, Track):
            raise TypeError("Can only compare Track objects")
        
        return DeepDiff(self.tags, other.tags)