import os
import sqlite3
from collections import defaultdict
from utilities import clean_genre_list

DEFAULT_SWINSIAN = os.path.expanduser('~/Library/Application Support/Swinsian/Library.sqlite')

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
        trackid_to_playlists = defaultdict(list)
        for playlist_id, track_id in playlisttrack_rows:
            name = playlist_id_to_name.get(playlist_id)
            if name and track_id in trackid_to_path:
                trackid_to_playlists[track_id].append(name)
        # Now build results
        for track_id, file_path in trackid_to_path.items():
            tag_dict = path_to_tagdict[file_path]
            playlists = trackid_to_playlists.get(track_id, [])
            genre_list = clean_genre_list(playlists)
            tags = {'path': [file_path], 'genre': genre_list}
            results[file_path] = tags
    finally:
        conn.close()
    return results

def write_swinsian_library(tracks, library_db_path=DEFAULT_SWINSIAN):
    """
    For each track, for each genre tag, ensure the track is in a playlist of the same name.
    If the playlist does not exist, create it. If the playlist-track association does not exist, create it.
    Remove any playlisttrack associations for that track that are not in its genre list.
    Also ensure every playlist is present in the topplaylist table so it shows up in Swinsian.
    Remove playlists (and their topplaylist entries) that are not referenced by any track's genre tag.
    Also updates the genre field in the tracks table with a comma-separated version of the genres.
    """
    conn = sqlite3.connect(library_db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT playlist_id, name FROM playlist")
        playlist_name_to_id = {name: pid for pid, name in cursor.fetchall()}
        cursor.execute("SELECT track_id, path FROM track")
        path_to_trackid = {path: tid for tid, path in cursor.fetchall()}
        cursor.execute("SELECT playlist_id, track_id FROM playlisttrack")
        playlisttrack_set = set(cursor.fetchall())
        cursor.execute("SELECT MAX(playlist_id) FROM playlist")
        max_pid = cursor.fetchone()[0] or 0
        next_pid = max_pid + 1
        used_playlist_ids = set()
        for file_path, tags in tracks.items():
            track_id = path_to_trackid.get(file_path)
            if not track_id:
                continue
            genres = set(tags.get('genre', []))
            # Update the genre field in the tracks table with a comma-separated version of the genres
            genre_str = ', '.join(sorted(genres))
            cursor.execute("UPDATE track SET genre = ? WHERE track_id = ?", (genre_str, track_id))
            genre_pids = set()
            for genre in genres:
                if not genre:
                    continue
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
                if (pid, track_id) not in playlisttrack_set:
                    cursor.execute(
                        "INSERT INTO playlisttrack (playlist_id, track_id, tindex) VALUES (?, ?, 0)",
                        (pid, track_id)
                    )
                    playlisttrack_set.add((pid, track_id))
            for (pid, tid) in list(playlisttrack_set):
                if tid == track_id and pid not in genre_pids:
                    cursor.execute(
                        "DELETE FROM playlisttrack WHERE playlist_id = ? AND track_id = ?",
                        (pid, track_id)
                    )
                    playlisttrack_set.remove((pid, track_id))
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
        all_playlist_ids = set(playlist_name_to_id.values())
        unused_playlist_ids = all_playlist_ids - used_playlist_ids
        for pid in unused_playlist_ids:
            cursor.execute("DELETE FROM topplaylist WHERE playlist_id = ?", (pid,))
            cursor.execute("DELETE FROM playlist WHERE playlist_id = ?", (pid,))
        conn.commit()
    finally:
        conn.close() 