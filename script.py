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

def clean_genre_list(genre_list):
    """
    Split genre strings on commas, remove duplicates, and sort alphabetically
    """
    genre_split = [g.strip() for genre in genre_list for g in genre.split(',')]
    return sorted(set(genre_split))

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
            # tags = {k: [str(v)] for k, v in tag_dict.items() if v is not None}
            # Add playlists to genre tag
            playlists = trackid_to_playlists.get(track_id, [])
            # if 'genre' in tags:
            #     # Append playlists to genre list
            #     tags['genre'] = tags['genre'] + playlists
            # else:
            #     tags['genre'] = playlists
            # Only sync genre tags
            genre_list = clean_genre_list(playlists)
            tags = {'path': [file_path], 'genre': genre_list}
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
    For each track, for each genre tag, ensure the track is in a playlist of the same name.
    If the playlist does not exist, create it. If the playlist-track association does not exist, create it.
    Remove any playlisttrack associations for that track that are not in its genre list.
    Also ensure every playlist is present in the topplaylist table so it shows up in Swinsian.
    Remove playlists (and their topplaylist entries) that are not referenced by any track's genre tag.
    """
    import sqlite3
    conn = sqlite3.connect(library_db_path)
    cursor = conn.cursor()
    try:
        # Get all playlists and build name->id mapping
        cursor.execute("SELECT playlist_id, name FROM playlist")
        playlist_name_to_id = {name: pid for pid, name in cursor.fetchall()}
        # Get all tracks and build path->track_id mapping
        cursor.execute("SELECT track_id, path FROM track")
        path_to_trackid = {path: tid for tid, path in cursor.fetchall()}
        # Get all playlisttrack associations as a set of (playlist_id, track_id)
        cursor.execute("SELECT playlist_id, track_id FROM playlisttrack")
        playlisttrack_set = set(cursor.fetchall())
        # Find max playlist_id for new inserts
        cursor.execute("SELECT MAX(playlist_id) FROM playlist")
        max_pid = cursor.fetchone()[0] or 0
        next_pid = max_pid + 1
        # For each track, for each genre, ensure association
        used_playlist_ids = set()
        for file_path, tags in tracks.items():
            track_id = path_to_trackid.get(file_path)
            if not track_id:
                continue
            genres = set(tags.get('genre', []))
            # Update the genre field in the tracks table with a comma-separated version of the genres
            genre_str = ', '.join(sorted(genres))
            cursor.execute("UPDATE track SET genre = ? WHERE track_id = ?", (genre_str, track_id))
            # Ensure all genre playlists exist and associations are present
            genre_pids = set()
            for genre in genres:
                if not genre:
                    continue
                # Ensure playlist exists
                if genre not in playlist_name_to_id:
                    cursor.execute(
                        "INSERT INTO playlist (playlist_id, name, pindex, folder, expanded) VALUES (?, ?, 0, 0, 0)",
                        (next_pid, genre)
                    )
                    playlist_name_to_id[genre] = next_pid
                    pid = next_pid
                    next_pid += 1
                else:
                    pid = playlist_name_to_id[genre]
                genre_pids.add(pid)
                used_playlist_ids.add(pid)
                # Ensure association exists
                if (pid, track_id) not in playlisttrack_set:
                    cursor.execute(
                        "INSERT INTO playlisttrack (playlist_id, track_id, tindex) VALUES (?, ?, 0)",
                        (pid, track_id)
                    )
                    playlisttrack_set.add((pid, track_id))
            # Remove associations for this track that are not in its genre list
            for (pid, tid) in list(playlisttrack_set):
                if tid == track_id and pid not in genre_pids:
                    cursor.execute(
                        "DELETE FROM playlisttrack WHERE playlist_id = ? AND track_id = ?",
                        (pid, track_id)
                    )
                    playlisttrack_set.remove((pid, track_id))
        # Ensure every playlist is present in topplaylist
        cursor.execute("SELECT playlist_id FROM topplaylist")
        topplaylist_pids = set(row[0] for row in cursor.fetchall())
        cursor.execute("SELECT MAX(topplaylist_id), MAX(pindex) FROM topplaylist")
        max_topplaylist_id, max_pindex = cursor.fetchone()
        next_topplaylist_id = (max_topplaylist_id or 0) + 1
        next_pindex = (max_pindex or 0) + 1
        for pid in set(playlist_name_to_id.values()):
            if pid not in topplaylist_pids and pid in used_playlist_ids:
                cursor.execute(
                    "INSERT INTO topplaylist (topplaylist_id, pindex, playlist_id) VALUES (?, ?, ?)",
                    (next_topplaylist_id, next_pindex, pid)
                )
                next_topplaylist_id += 1
                next_pindex += 1
        # Remove playlists and topplaylist entries not used
        all_playlist_ids = set(playlist_name_to_id.values())
        unused_playlist_ids = all_playlist_ids - used_playlist_ids
        for pid in unused_playlist_ids:
            cursor.execute("DELETE FROM topplaylist WHERE playlist_id = ?", (pid,))
            cursor.execute("DELETE FROM playlist WHERE playlist_id = ?", (pid,))
        conn.commit()
    finally:
        conn.close()

def write_music_folder(tracks, library_dir):
    """
    For each track, if the file is in library_dir, write the genre tag (comma-separated string) to the ID3 tag.
    """
    import os
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


def write_yaml(tracks, library_dir):
    """
    Writes YAML files for each file_path in tracks.
    """
    yaml_dir = os.path.join(library_dir, '.djtag')
    # Delete all files in djtag_dir except .gitignore
    print("Resetting .djtag folder...")
    for file in os.listdir(yaml_dir):
        if file != '.gitignore' and file != '.git':
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

    # print("Pulling tags from ID3...")
    # id3_tracks = scan_music_folder(library_dir)
    # write_yaml(id3_tracks, library_dir)
    # print("Committing id3 tags to git...")
    # commit_yaml_to_git(djtag_dir, 'id3')

    print("Pulling tags from Swinsian...")
    swinsian_tracks = scan_swinsian_library()
    write_yaml(swinsian_tracks, library_dir)
    print("Committing swinsian tags to git...")
    commit_yaml_to_git(djtag_dir, 'swinsian')

    # TODO: git_merge_id3_swinsian()
    
    print("Scanning merged YAML files...")
    yaml_tracks = scan_yaml(library_dir)
    print("Writing Swinsian library...")
    write_swinsian_library(yaml_tracks)
    # print("Writing id3 tags in music folder...")
    # write_music_folder(yaml_tracks, library_dir)

if __name__ == '__main__':
    main() 