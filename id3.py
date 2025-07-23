import os
from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError
from utilities import clean_genre_list

def is_music_file(filename):
    return any(filename.lower().endswith(ext) for ext in ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac'])

def scan_music_folder(folder_path):
    """
    Scans a folder for music files and returns a dict:
    {file_path: tags}
    """
    id3_data = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            if is_music_file(file):
                file_path = os.path.join(root, file)
                try:
                    tags = dict(EasyID3(file_path))
                    tags['path'] = [file_path]
                    if 'genre' in tags:
                        tags['genre'] = clean_genre_list(tags['genre'])
                    id3_data[file_path] = tags
                except ID3NoHeaderError:
                    id3_data[file_path] = {'path': [file_path]}
    return id3_data

def write_music_folder(tracks, library_dir):
    """
    For each track, if the file is in library_dir, write the genre tag (comma-separated string) to the ID3 tag.
    """
    for file_path, tags in tracks.items():
        abs_file_path = os.path.abspath(file_path)
        abs_library_dir = os.path.abspath(library_dir)
        # Check if file exists and is within library_dir
        if not os.path.isfile(abs_file_path):
            print(f"File does not exist: {file_path}")
            continue
        if not os.path.commonpath([abs_file_path, abs_library_dir]) == abs_library_dir:
            print(f"Skipping {file_path} (not in library_dir)")
            continue
        genres = tags.get('genre', [])
        genre_str = ', '.join(genres)
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
                continue
        id3_tags['genre'] = genre_str
        try:
            id3_tags.save()
            print(f"Updated genre for {file_path} -> {genre_str}")
        except Exception as e:
            print(f"Failed to save ID3 for {file_path}: {e}") 