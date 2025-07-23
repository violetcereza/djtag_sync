import os
from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError
import yaml
import subprocess

MUSIC_EXTENSIONS = ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac']
DEFAULT_SWINSIAN = os.path.expanduser('~/Library/Application Support/Swinsian/Library.sqlite')
# DEFAULT_SERATO = os.path.expanduser('~/Music/_Serato_/Subcrates')

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
    Scans a folder for music files and returns a dict:
    {file_path: tags}
    """
    id3_data = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            if is_music_file(file):
                file_path = os.path.join(root, file)
                try:
                    tags = EasyID3(file_path)
                    id3_data[file_path] = dict(tags)
                except ID3NoHeaderError:
                    id3_data[file_path] = {}
                except Exception as e:
                    id3_data[file_path] = {'error': str(e)}
    return id3_data

def scan_swinsian_library(library_db_path=DEFAULT_SWINSIAN):
    """
    Scans a Swinsian SQLite library and returns a dict:
    {file_path: tags}
    
    # Swinsian 'track' table fields (as of 2024-06):
    # track_id, title, artist, album, genre, composer, year, tracknumber, discnumber, bitrate, 
    # bitdepth, samplerate, channels, length, dateadded, lastplayed, playcount, rating, filesize, 
    # enabled, cue, gapless, compilation, encoder, path, filename, comment, properties_id, 
    # albumartist, totaldiscnumber, datecreated, grouping, bpm, publisher, totaltracknumber, 
    # description, datemodified, catalognumber, conductor, discsubtitle, lyrics, copyright
    """
    import sqlite3

    results = {}
    conn = sqlite3.connect(library_db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM track")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            file_path = row_dict.get('path', '') or ''  # path includes filename
            tags = {k: [str(v)] for k, v in row_dict.items() if v is not None and k != 'path'}
            results[file_path] = tags
    finally:
        conn.close()
    return results


def commit_djtag_to_git(djtag_dir, source):
    """
    Stages and commits all changes in the .djtag directory to git.
    """

    try:
        # Stage all changes in .djtag
        subprocess.run(['git', 'add', djtag_dir], cwd=djtag_dir, check=True)
        # Commit with a message
        subprocess.run(['git', 'commit', '-m', f'djtag: update from {source}'], cwd=djtag_dir, check=True)
        print("Committed .djtag folder to git.")
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed: {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Scan a folder for music files and aggregate ID3 data.')
    parser.add_argument('--folder', help='Path to the folder to scan', 
        default='~/Dropbox/Cloud Music/Testing DJ Library')
    
    args = parser.parse_args()
    library_dir = os.path.expanduser(args.folder)
    djtag_dir = os.path.join(library_dir, '.djtag')

    # TODO: check that git repo is set up with .gitignore

    try:
        original_commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd=djtag_dir
        ).decode('utf-8').strip()
        print(f"Current git HEAD hash: {original_commit}")
    except Exception as e:
        print(f"Could not get git HEAD hash: {e}")

    print("Pulling tags from ID3...")
    id3_tracks = scan_music_folder(library_dir)
    for file_path, tags in id3_tracks.items():
        save_tags_yaml(library_dir, file_path, tags)
        print(f"♫  {os.path.relpath(file_path, library_dir)}")

    print("Committing .djtag folder to git...")
    commit_djtag_to_git(djtag_dir, 'ID3')

    # Git checkout HEAD^ 
    print(f"Checking out original_commit...")
    subprocess.run(['git', 'checkout', original_commit], cwd=djtag_dir, check=True)

    # Apply the Swinsian mapping to the working tree
    print("Pulling tags from Swinsian...")
    swinsian_tracks = scan_swinsian_library()
    for file_path, tags in swinsian_tracks.items():
        if file_path in id3_tracks:
            save_tags_yaml(library_dir, file_path, tags)
            print(f"♫  {os.path.relpath(file_path, library_dir)}")
        else:
            print(f"No ID3 tags found for {file_path}")

    print("Committing .djtag folder to git...")
    commit_djtag_to_git(djtag_dir, 'Swinsian')

    # TODO: merge the commits
    # TODO: push the changes to the remote repo

if __name__ == '__main__':
    main() 