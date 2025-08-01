import os
from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError
from utilities import clean_genre_list
from track import Track
from library import DJLibrary

class ID3Library(DJLibrary):
    """
    A library for reading and writing ID3 tags from a music directory.
    """
    
    def __init__(self, music_folder):
        """
        Initialize the ID3Library with a directory path and scan for tracks.
        
        Args:
            music_folder (str): Path to the music library directory
        """
        super().__init__(music_folder)
    
    @staticmethod
    def is_music_file(filename):
        """Check if a file is a supported music file."""
        return any(filename.lower().endswith(ext) for ext in ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac'])
    
    def _scan(self):
        """
        Scans the library directory for music files and returns a dict:
        {file_path: Track instance}
        """
        print(f"Scanning {self.music_folder}")
        tracks = {}
        for root, _, files in os.walk(self.music_folder):
            for file in files:
                if self.is_music_file(file):
                    file_path = os.path.join(root, file)
                    try:
                        tags_dict = dict(EasyID3(file_path))
                        if 'genre' in tags_dict:
                            tags_dict['genre'] = clean_genre_list(tags_dict['genre'])
                        # Convert list values to strings for Track compatibility
                        # tags = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in tags_dict.items()}
                        tracks[file_path] = Track(file_path, tags_dict)
                    except ID3NoHeaderError:
                        tracks[file_path] = Track(file_path, {})
        return tracks
    
    def write(self, track):
        """
        Write the track's genre tag to the ID3 file if it's in the library directory.
        
        Args:
            track (Track): Track instance to write
        """
        file_path = track.path
        abs_file_path = os.path.abspath(file_path)
        # Check if file exists and is within library_dir
        if not os.path.isfile(abs_file_path):
            print(f"File does not exist: {file_path}")
            return
        if not os.path.commonpath([abs_file_path, self.library_dir]) == self.library_dir:
            print(f"Skipping {file_path} (not in library_dir)")
            return
        genre_str = track.tags.get('genre', '')
        if not isinstance(genre_str, str):
            genre_str = ', '.join(genre_str) if genre_str else ''
        try:
            id3_tags = EasyID3(abs_file_path)
        except Exception:
            # If no ID3 header, try to add one
            try:
                id3_tags = EasyID3()
                id3_tags.save(abs_file_path)
                id3_tags = EasyID3(abs_file_path)
            except Exception as e:
                print(f"Could not open or create ID3 for {file_path}: {e}")
                return
        id3_tags['genre'] = genre_str
        try:
            id3_tags.save()
            print(f"Updated genre for {file_path} -> {genre_str}")
        except Exception as e:
            print(f"Failed to save ID3 for {file_path}: {e}")
    
    def writeLibrary(self):
        """
        Write all tracks in the library to their respective ID3 files.
        """
        for file_path, track in self.tracks.items():
            self.write(track) 