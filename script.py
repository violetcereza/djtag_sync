import os
from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError
import yaml
import subprocess

MUSIC_EXTENSIONS = ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac']
DEFAULT_SWINSIAN = os.path.expanduser('~/Library/Application Support/Swinsian/Library.sqlite')
DEFAULT_SERATO = os.path.expanduser('~/Music/_Serato_/Subcrates')

def is_music_file(filename):
    return any(filename.lower().endswith(ext) for ext in MUSIC_EXTENSIONS)

def save_tags_yaml(folder_path, file_path, tags):
    djtag_dir = os.path.join(folder_path, '.djtag')
    rel_path = os.path.relpath(file_path, folder_path)
    base_name, _ = os.path.splitext(rel_path)
    yaml_path = os.path.join(djtag_dir, f'{base_name}.yaml')
    yaml_dir = os.path.dirname(yaml_path)
    os.makedirs(yaml_dir, exist_ok=True)
    with open(yaml_path, 'w') as f:
        yaml.dump(tags, f, allow_unicode=True)

def scan_music_folder(folder_path):
    """
    Scans a folder for music files and returns a list of dicts:
    {file: file_path, tags: metadata}
    """
    id3_data = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if is_music_file(file):
                file_path = os.path.join(root, file)
                try:
                    tags = EasyID3(file_path)
                    id3_data.append({'file': file_path, 'tags': dict(tags)})
                except ID3NoHeaderError:
                    id3_data.append({'file': file_path, 'tags': {}})
                except Exception as e:
                    id3_data.append({'file': file_path, 'error': str(e)})
    return id3_data

def scan_swinsian_library(library_db_path=DEFAULT_SWINSIAN):
    """
    Scans a Swinsian SQLite library and returns a list of dicts:
    {file: file_path, tags: metadata}
    """
    import sqlite3

    results = []
    conn = sqlite3.connect(library_db_path)
    cursor = conn.cursor()
    try:
        # Swinsian's main table is usually 'tracks'
        cursor.execute("SELECT location, title, artist, album, genre, year, track, disc, comment, bpm FROM tracks")
        for row in cursor.fetchall():
            location, title, artist, album, genre, year, track, disc, comment, bpm = row
            # Swinsian stores file URLs as 'file://...'
            if location and location.startswith('file://'):
                # Convert file URL to path
                from urllib.parse import unquote, urlparse
                parsed = urlparse(location)
                file_path = unquote(parsed.path)
            else:
                file_path = location or ""
            tags = {}
            if title: tags['title'] = [title]
            if artist: tags['artist'] = [artist]
            if album: tags['album'] = [album]
            if genre: tags['genre'] = [genre]
            if year: tags['date'] = [str(year)]
            if track: tags['tracknumber'] = [str(track)]
            if disc: tags['discnumber'] = [str(disc)]
            if comment: tags['comment'] = [comment]
            if bpm: tags['bpm'] = [str(bpm)]
            results.append({'file': file_path, 'tags': tags})
    finally:
        conn.close()
    return results


def commit_djtag_to_git(library_dir):
    """
    Stages and commits all changes in the .djtag directory to git.
    """
    import subprocess
    djtag_dir = os.path.join(library_dir, '.djtag')

    try:
        # Stage all changes in .djtag
        subprocess.run(['git', 'add', djtag_dir], cwd=djtag_dir, check=True)
        # Commit with a message
        subprocess.run(['git', 'commit', '-m', 'djtag: update from ID3'], cwd=djtag_dir, check=True)
        print("Committed .djtag folder to git.")
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scan a folder for music files and aggregate ID3 data.')
    parser.add_argument('folder', help='Path to the folder to scan')
    
    args = parser.parse_args()
    library_dir = args.folder

    print("Pulling tags from ID3...")
    id3_tracks = scan_music_folder(library_dir)
    for track in id3_tracks:
        save_tags_yaml(library_dir, track['file'], track['tags'])
        print(f"-  {os.path.relpath(track['file'], library_dir)}")

    # TODO: check that git repo is set up with .gitignore

    # Git commit the .djtag folder
    print("Committing .djtag folder to git...")
    commit_djtag_to_git(library_dir)
    
    print("Pulling tags from Swinsian...")
    swinsian_tracks = scan_swinsian_library()
    for track in swinsian_tracks:
        save_tags_yaml(library_dir, track['file'], track['tags'])
        print(f"-  {os.path.relpath(track['file'], library_dir)}")

    # TODO: merge the commits
    # TODO: push the changes to the remote repo

if __name__ == '__main__':
    main() 