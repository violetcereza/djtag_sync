import os
from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError
import yaml
import subprocess
from datetime import datetime
import shutil

MUSIC_EXTENSIONS = ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac']
DEFAULT_SWINSIAN = os.path.expanduser('~/Library/Application Support/Swinsian/Library.sqlite')
# DEFAULT_SERATO = os.path.expanduser('~/Music/_Serato_/Subcrates')

def is_music_file(filename):
    return any(filename.lower().endswith(ext) for ext in MUSIC_EXTENSIONS)

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
                    id3_data[file_path] = tags
                except ID3NoHeaderError:
                    id3_data[file_path] = {'path': [file_path]}
                # except Exception as e:
                #     id3_data[file_path] = {'error': str(e)}
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
        track_rows = cursor.fetchall()

        # Build track_id -> file_path and row_dict
        trackid_to_path = {}
        path_to_tagdict = {}
        for row in track_rows:
            tag_dict = dict(zip(columns, row))
            file_path = tag_dict.get('path', '') or ''
            track_id = tag_dict.get('track_id')
            trackid_to_path[track_id] = file_path
            path_to_tagdict[file_path] = tag_dict

        # Get all playlist names
        cursor.execute("SELECT playlist_id, name FROM playlist")
        playlist_id_to_name = {pid: name for pid, name in cursor.fetchall()}

       # Get all playlist-track associations
        cursor.execute("SELECT playlist_id, track_id FROM playlisttrack")
        playlisttrack_rows = cursor.fetchall()

        # Build track_id -> list of playlist names
        from collections import defaultdict
        trackid_to_playlists = defaultdict(list)
        for playlist_id, track_id in playlisttrack_rows:
            name = playlist_id_to_name.get(playlist_id)
            if name and track_id in trackid_to_path:
                trackid_to_playlists[track_id].append(name)

        # Now build results
        for track_id, file_path in trackid_to_path.items():
            tag_dict = path_to_tagdict[file_path]
            # Format the tags as a dict of lists of strings
            tags = {k: [str(v)] for k, v in tag_dict.items() if v is not None}
            # Add playlists to genre tag
            playlists = trackid_to_playlists.get(track_id, [])
            if playlists:
                if 'genre' in tags:
                    # Append playlists to genre list
                    tags['genre'] = tags['genre'] + playlists
                else:
                    tags['genre'] = playlists
            results[file_path] = tags
    finally:
        conn.close()
    return results

def scan_yaml(library_dir):
    """
    Scans the .djtag folder for YAML files and returns a dict:
    {file_path: tags}
    """
    yaml_dir = os.path.join(library_dir, '.djtag')
    yaml_tracks = {}
    for root, _, files in os.walk(yaml_dir):
        for file in files:
            if file.endswith('.yaml'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    tags = yaml.load(f, Loader=yaml.SafeLoader)
                yaml_tracks[tags['path'][0]] = tags
    return yaml_tracks


def write_swinsian_library(tracks, library_db_path=DEFAULT_SWINSIAN):
    """
    Writes a Swinsian library from a dict of {file_path: tags}.
    """

    # TODO: write the library

    
def write_yaml(tracks, library_dir):
    """
    Writes YAML files for each file_path in tracks.
    """
    yaml_dir = os.path.join(library_dir, '.djtag')
    # Delete all files in djtag_dir except .gitignore
    for file in os.listdir(yaml_dir):
        if file != '.gitignore' and file != '.git':
            print(f"Deleting {file}")
            path = os.path.join(yaml_dir, file)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    
    for file_path, tags in tracks.items():
        if not os.path.commonpath([os.path.abspath(file_path), os.path.abspath(library_dir)]) == \
            os.path.abspath(library_dir):
            print(f"Skipping {file_path} because it's not in the library directory")
            continue

        rel_path = os.path.relpath(file_path, library_dir)
        base_name, _ = os.path.splitext(rel_path)
        yaml_path = os.path.join(yaml_dir, f'{base_name}.yaml')
        internal_yaml_dir = os.path.dirname(yaml_path)
        os.makedirs(internal_yaml_dir, exist_ok=True)
        with open(yaml_path, 'w') as f:
            yaml.dump(tags, f, allow_unicode=True)
        print(f"♫  {os.path.relpath(file_path, library_dir)}")


def commit_yaml_to_git(djtag_dir, branch):
    """
    Checks out the named branch (creating it if it doesn't exist) without changing the working tree, 
    then commits all changes in .djtag on that branch.
    """
    # Check if branch exists
    if branch != 'id3':
        result = subprocess.run(['git', 'rev-parse', '--verify', branch], 
            cwd=djtag_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode != 0:
            # Branch does not exist, create it from id3 branch
            subprocess.run(['git', 'checkout', '-b', branch, 'id3'], cwd=djtag_dir, check=True)
    
    # Set the HEAD to the named branch
    try:
        subprocess.run(['git', 'symbolic-ref', 'HEAD', f"refs/heads/{branch}"], cwd=djtag_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Git branch checkout/switch failed: {e}")
        return

    # Stage and commit
    try:
        subprocess.run(['git', 'add', djtag_dir], cwd=djtag_dir, check=True)
        subprocess.run(['git', 'commit', '-m', 
            f'djtag: update from {branch}, {datetime.now().strftime("%Y-%m-%d")}'], cwd=djtag_dir, check=True)
        print(f"Committed .djtag folder to git on branch {branch}.")
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

    # try:
    #     original_commit = subprocess.check_output(
    #         ['git', 'rev-parse', 'HEAD'],
    #         cwd=djtag_dir
    #     ).decode('utf-8').strip()
    #     print(f"Current git HEAD hash: {original_commit}")
    # except Exception as e:
    #     print(f"Could not get git HEAD hash: {e}")

    print("Pulling tags from ID3...")
    id3_tracks = scan_music_folder(library_dir)
    write_yaml(id3_tracks, library_dir)

    # print("Committing id3 tags to git...")
    # commit_yaml_to_git(djtag_dir, 'id3')

    # # Git checkout HEAD^ 
    # print(f"Checking out original_commit...")
    # subprocess.run(['git', 'checkout', original_commit], cwd=djtag_dir, check=True)

    # Apply the Swinsian mapping to the working tree
    print("Pulling tags from Swinsian...")
    swinsian_tracks = scan_swinsian_library()
    write_yaml(swinsian_tracks, library_dir)

    # print("Committing swinsian tags to git...")
    # commit_yaml_to_git(djtag_dir, 'swinsian')

    # TODO: git_merge_id3_swinsian()
    
    print("Scanning merged YAML files...")
    yaml_tracks = scan_yaml(library_dir)
    print(yaml_tracks)
    # write_swinsian_library(yaml_tracks)

if __name__ == '__main__':
    main() 