#!/usr/bin/env python3

import sqlite3
import argparse
import sys
import struct
from typing import Optional, Dict, Any, List


class TracksByBPM:
    def __init__(self, database_path: str):
        self.database_path = database_path
    
    def parse_tsaf_blob(self, data: bytes) -> Dict[str, Any]:
        """Parse TSAF blob to extract all possible key-value pairs, splitting on 0x00 0x08 and 0x00.type, decoding as UTF-8."""
        properties = {}
        all_strings = []
        string_spans = []  # (string, preceding_bytes)
        seps = [b'\x00\x08', b'\x00\x2e\x08type\x00\x0c\x00\x1c\x00\x00\x00\x08']
        start = 0
        last_sep = 0
        i = 0
        while i <= len(data):
            found_sep = None
            for sep in seps:
                if i + len(sep) <= len(data) and data[i:i+len(sep)] == sep:
                    found_sep = sep
                    break
            if i == len(data) or found_sep:
                chunk = data[start:i]
                try:
                    s = chunk.decode('utf-8').strip()
                except Exception:
                    s = ''
                if s:
                    all_strings.append(s)
                    string_spans.append((s, data[last_sep:start].hex()))
                if i == len(data):
                    break
                last_sep = i
                start = i + len(found_sep) if found_sep else i
                i = start
            else:
                i += 1
        properties['all_strings'] = all_strings
        properties['string_spans'] = [(s, preceding_bytes) for s, preceding_bytes in string_spans]
        # Flexible key-value extraction: for each known key, get the value before it
        known_keys = [
            'name', 'uuid', 'artist', 'album', 'genre', 'composer', 'year', 'trackNumber', 'albumTrackNumber',
            'discNumber', 'grouping', 'comments', 'contentType', 'file', 'originSourceID', 'titleID',
            'artistUUIDs', 'albumUUID', 'genreUUIDs', 'playlistUUID', 'mediaItemUUID', 'parentUUID', 'type',
            'itemUUIDs', 'title', 'manualBPM', 'bpm', 'duration', 'sampleRate', 'bitRate', 'keySignatureIndex'
        ]
        for i, s in enumerate(all_strings):
            if s in known_keys and i > 0:
                key = s
                value = all_strings[i-1]
                if key in ['year', 'trackNumber', 'albumTrackNumber', 'discNumber', 'keySignatureIndex']:
                    try:
                        value = int(value)
                    except Exception:
                        pass
                elif key in ['bpm', 'manualBPM', 'duration', 'sampleRate', 'bitRate']:
                    try:
                        value = float(value)
                    except Exception:
                        pass
                properties[key] = value
        # uuids = [s for s in all_strings if len(s) == 36 and s.count('-') == 4]
        # if uuids:
        #     properties['uuids'] = uuids
        properties = {k: v for k, v in properties.items() if v is not None}
        return properties
    
    # def get_playlists_for_track(self, track_key: str, cursor: sqlite3.Cursor) -> List[str]:
    #     """Get all playlists that contain a specific track."""
    #     playlists = []
        
    #     try:
    #         # First, get the track's UUID from the mediaItems collection
    #         cursor.execute(
    #             "SELECT data FROM database2 WHERE collection = 'mediaItems' AND key = ?",
    #             (track_key,)
    #         )
    #         result = cursor.fetchone()
    #         if not result or not result[0]:
    #             return []
            
    #         # Parse the track's TSAF data to get its UUID
    #         track_props = self.parse_tsaf_blob(result[0])
    #         track_uuid = track_props.get('uuid')
    #         if not track_uuid:
    #             return []
            
    #         # Find playlist items that reference this track UUID
    #         cursor.execute(
    #             "SELECT data FROM database2 WHERE collection = 'mediaItemPlaylistItems' AND data LIKE ?",
    #             (f'%{track_uuid}%',)
    #         )
    #         playlist_item_results = cursor.fetchall()
            
    #         for item_result in playlist_item_results:
    #             if item_result[0]:
    #                 try:
    #                     item_props = self.parse_tsaf_blob(item_result[0])
    #                     playlist_uuid = item_props.get('playlistUUID')
                        
    #                     if playlist_uuid:
    #                         # Find the playlist with this UUID
    #                         cursor.execute(
    #                             "SELECT data FROM database2 WHERE collection = 'mediaItemPlaylists' AND data LIKE ?",
    #                             (f'%{playlist_uuid}%',)
    #                         )
    #                         playlist_result = cursor.fetchone()
                            
    #                         if playlist_result and playlist_result[0]:
    #                             try:
    #                                 playlist_props = self.parse_tsaf_blob(playlist_result[0])
    #                                 playlist_name = playlist_props.get('name')
                                    
    #                                 if playlist_name:
    #                                     # Try to get the name from the index first
    #                                     cursor.execute(
    #                                         "SELECT name FROM secondaryIndex_mediaItemPlaylistIndex WHERE rowid = ?",
    #                                         (playlist_uuid,)
    #                                     )
    #                                     index_result = cursor.fetchone()
                                        
    #                                     if index_result and index_result[0]:
    #                                         playlists.append(index_result[0])
    #                                     else:
    #                                         # If not in index, use the name from TSAF
    #                                         playlists.append(playlist_name)
                                            
    #                             except Exception as e:
    #                                 continue
                                    
    #                 except Exception as e:
    #                     continue
            
    #     except sqlite3.Error as e:
    #         # If query fails, return empty list
    #         pass
        
    #     return list(set(playlists))  # Remove duplicates
    
    # def get_track_metadata(self, rowid: int, cursor: sqlite3.Cursor) -> Dict[str, Any]:
    #     """Get track metadata for a given rowid."""
    #     # Get the key from mediaItemAnalyzedData collection
    #     cursor.execute(
    #         "SELECT key FROM database2 WHERE rowid = ? AND collection = 'mediaItemAnalyzedData'",
    #         (rowid,)
    #     )
    #     result = cursor.fetchone()
    #     if not result:
    #         return {}
        
    #     key = result[0]
        
    #     # Get the corresponding mediaItems entry
    #     cursor.execute(
    #         "SELECT rowid FROM database2 WHERE collection = 'mediaItems' AND key = ?",
    #         (key,)
    #     )
    #     result = cursor.fetchone()
    #     if not result:
    #         return {}
        
    #     media_rowid = result[0]
        
    #     # Get the BLOB data
    #     cursor.execute("SELECT data FROM database2 WHERE rowid = ?", (media_rowid,))
    #     result = cursor.fetchone()
    #     if not result or not result[0]:
    #         return {}
        
    #     blob_data = result[0]
    #     properties = self.parse_tsaf_blob(blob_data)
        
    #     # Add playlist information
    #     playlists = self.get_playlists_for_track(key, cursor)
    #     if playlists:
    #         properties['playlists'] = playlists
        
    #     return properties
    
    # def list_tracks_by_bpm_with_metadata(self, limit: int = 50, show_all_properties: bool = False):
    #     """List tracks sorted by BPM with metadata."""
    #     print("Tracks sorted by BPM (with metadata):")
    #     print("=====================================")
        
    #     try:
    #         conn = sqlite3.connect(self.database_path)
    #         cursor = conn.cursor()
            
    #         # Query tracks by BPM
    #         query = """
    #             SELECT rowid, bpm, manualBPM, keySignatureIndex 
    #             FROM secondaryIndex_mediaItemAnalyzedDataIndex 
    #             WHERE bpm IS NOT NULL 
    #             ORDER BY bpm 
    #             LIMIT ?
    #         """
            
    #         cursor.execute(query, (limit,))
    #         tracks = cursor.fetchall()
            
    #         if not tracks:
    #             print("No tracks with BPM data found.")
    #             return
            
    #         track_count = 0
    #         for track in tracks:
    #             track_count += 1
    #             rowid, bpm, manual_bpm, key_signature_index = track
                
    #             # Get metadata for this track
    #             properties = self.get_track_metadata(rowid, cursor)
                
    #             print(f"{track_count}. Track rowid: {rowid}")
    #             print(f"   BPM: {bpm:.1f}")
    #             if manual_bpm and manual_bpm > 0:
    #                 print(f"   Manual BPM: {manual_bpm:.1f}")
                
    #             # Show key properties
    #             if properties.get('title'):
    #                 print(f"   Title: {properties['title']}")
    #             if properties.get('artist'):
    #                 print(f"   Artist: {properties['artist']}")
    #             if properties.get('album'):
    #                 print(f"   Album: {properties['album']}")
    #             if properties.get('genre'):
    #                 print(f"   Genre: {properties['genre']}")
    #             if properties.get('year'):
    #                 print(f"   Year: {properties['year']}")
    #             if properties.get('track_number'):
    #                 print(f"   Track Number: {properties['track_number']}")
    #             if properties.get('duration_seconds'):
    #                 print(f"   Duration: {properties['duration_seconds']:.1f}s")
    #             if properties.get('sample_rate'):
    #                 print(f"   Sample Rate: {properties['sample_rate']} Hz")
    #             if properties.get('bit_rate'):
    #                 print(f"   Bit Rate: {properties['bit_rate']} bps")
    #             if properties.get('playlists'):
    #                 print(f"   Playlists: {', '.join(properties['playlists'])}")
                
    #             print(f"   Key Signature Index: {key_signature_index}")
                
    #             # Show all properties if requested
    #             if show_all_properties:
    #                 print("   All Properties:")
    #                 for key, value in properties.items():
    #                     if key not in ['title', 'artist', 'album', 'genre', 'year', 'track_number', 'duration_seconds', 'sample_rate', 'bit_rate', 'playlists']:
    #                         print(f"     {key}: {value}")
                
    #             print()
            
    #         if track_count == limit:
    #             print(f"... showing first {limit} tracks. Use a higher limit to see more.")
            
    #         # Get total count
    #         cursor.execute("SELECT COUNT(*) FROM secondaryIndex_mediaItemAnalyzedDataIndex WHERE bpm IS NOT NULL")
    #         total = cursor.fetchone()[0]
    #         print(f"Total tracks with BPM data: {total}")
            
    #     except sqlite3.Error as e:
    #         print(f"Error querying BPM data: {e}")
    #     finally:
    #         if 'conn' in locals():
    #             conn.close()

    # def list_tracks_in_playlists(self, database_path: str, limit: int = 50):
    #     conn = sqlite3.connect(database_path)
    #     cursor = conn.cursor()
    #     print("Tracks in at least one playlist:")
    #     print("===============================")
    #     count = 0
    #     # Get all playlist items
    #     cursor.execute("SELECT data FROM database2 WHERE collection = 'mediaItemPlaylistItems'")
    #     playlist_items = cursor.fetchall()
    #     track_uuid_to_playlists = {}
    #     for item in playlist_items:
    #         if not item[0]:
    #             continue
    #         try:
    #             item_props = self.parse_tsaf_blob(item[0])
    #             track_uuid = item_props.get('mediaItemUUID')
    #             playlist_uuid = item_props.get('playlistUUID')
    #             if not track_uuid or not playlist_uuid:
    #                 continue
    #             if track_uuid not in track_uuid_to_playlists:
    #                 track_uuid_to_playlists[track_uuid] = set()
    #             track_uuid_to_playlists[track_uuid].add(playlist_uuid)
    #         except Exception:
    #             continue
    #     # For each track UUID, get metadata and playlist names
    #     for track_uuid, playlist_uuids in track_uuid_to_playlists.items():
    #         # Find the mediaItems key for this UUID
    #         cursor.execute("SELECT key, data FROM database2 WHERE collection = 'mediaItems'")
    #         found = False
    #         for key, data in cursor.fetchall():
    #             try:
    #                 props = self.parse_tsaf_blob(data)
    #                 if props.get('uuid') == track_uuid:
    #                     found = True
    #                     break
    #             except Exception:
    #                 continue
    #         if not found:
    #             continue
    #         properties = props
    #         # Get playlist names
    #         playlist_names = []
    #         for playlist_uuid in playlist_uuids:
    #             cursor.execute("SELECT name FROM secondaryIndex_mediaItemPlaylistIndex WHERE rowid = ?", (playlist_uuid,))
    #             result = cursor.fetchone()
    #             if result and result[0]:
    #                 playlist_names.append(result[0])
    #             else:
    #                 # Fallback: get from TSAF
    #                 cursor.execute("SELECT data FROM database2 WHERE collection = 'mediaItemPlaylists' AND data LIKE ?", (f'%{playlist_uuid}%',))
    #                 playlist_result = cursor.fetchone()
    #                 if playlist_result and playlist_result[0]:
    #                     try:
    #                         playlist_props = self.parse_tsaf_blob(playlist_result[0])
    #                         if playlist_props.get('name'):
    #                             playlist_names.append(playlist_props['name'])
    #                     except Exception:
    #                         continue
    #         print(f"Track UUID: {track_uuid}")
    #         if properties.get('title'):
    #             print(f"   Title: {properties['title']}")
    #         if properties.get('artist'):
    #             print(f"   Artist: {properties['artist']}")
    #         print(f"   Playlists: {', '.join(playlist_names)}")
    #         print()
    #         count += 1
    #         if count >= limit:
    #             print(f"... showing first {limit} tracks. Use a higher limit to see more.")
    #             break
    #     print(f"Total tracks in playlists: {count}")

    def debug_parse_blob_by_uuid(self, uuid: str):
        """Fetch and parse the BLOB for a given UUID from database2, searching all collections."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT collection, data FROM database2 WHERE key = ?",
            (uuid,)
        )
        result = cursor.fetchone()
        if not result or not result[1]:
            print(f"No BLOB found for UUID {uuid} in any collection")
            return
        collection, data = result
        props = self.parse_tsaf_blob(data)
        print(f"Parsed BLOB for UUID {uuid} in collection {collection}:")
        for k, v in props.items():
            if k == 'string_spans':
                print("  string_spans:")
                for s, sep in v:
                    print(f"    - '{s}' (preceding bytes: {sep})")
            else:
                print(f"  {k}: {v}")
        conn.close()

    def extract_all_playlist_mappings(self):
        """Extract and print all playlist-to-track mappings from the database, using itemUUIDs from mediaItemPlaylists."""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        # Build track UUID to title mapping
        cursor.execute("SELECT data FROM database2 WHERE collection = 'mediaItems'")
        track_uuid_to_title = {}
        for (data,) in cursor.fetchall():
            try:
                props = self.parse_tsaf_blob(data)
                uuid = props.get('uuid')
                title = props.get('title')
                if uuid and title:
                    track_uuid_to_title[uuid] = title
            except Exception:
                continue
        # Build itemUUID to mediaItemUUID mapping
        cursor.execute("SELECT key, data FROM database2 WHERE collection = 'mediaItemPlaylistItems'")
        itemuuid_to_trackuuid = {}
        for key, data in cursor.fetchall():
            try:
                props = self.parse_tsaf_blob(data)
                media_item_uuid = props.get('mediaItemUUID')
                if media_item_uuid:
                    itemuuid_to_trackuuid[key] = media_item_uuid
            except Exception:
                continue
        # Extract all playlists and their itemUUIDs
        cursor.execute("SELECT key, data FROM database2 WHERE collection = 'mediaItemPlaylists'")
        playlist_mappings = {}
        for key, data in cursor.fetchall():
            try:
                props = self.parse_tsaf_blob(data)
                uuid = props.get('uuid') or key
                name = props.get('name') or uuid
                all_strings = props.get('all_strings', [])
                item_uuids = []
                try:
                    itemuuids_idx = all_strings.index('itemUUIDs')
                    item_uuids = all_strings[7:itemuuids_idx]
                except Exception:
                    pass
                playlist_mappings[(name, uuid)] = item_uuids
            except Exception:
                continue
        # Print mappings
        for (playlist_name, playlist_uuid), item_uuids in playlist_mappings.items():
            print(f"Playlist: {playlist_name} ({playlist_uuid})")
            for item_uuid in item_uuids:
                track_uuid = itemuuid_to_trackuuid.get(item_uuid)
                if track_uuid:
                    title = track_uuid_to_title.get(track_uuid)
                    if title:
                        print(f"  - {title} ({track_uuid})")
                    else:
                        print(f"  - [NO TITLE FOUND] ({track_uuid})")
                else:
                    print(f"  - [NO TRACK UUID FOUND] ({item_uuid})")
            print()
        print(f"Total playlists: {len(playlist_mappings)}")
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="List tracks by BPM from djay database")
    parser.add_argument("database_path", help="Path to the djay database file")
    parser.add_argument("--limit", type=int, default=50, help="Number of tracks to show (default: 50)")
    parser.add_argument("--show-all-properties", action="store_true", 
                       help="Show all extracted properties for each track")
    parser.add_argument("--tracks-by-bpm-with-metadata", action="store_true", 
                       help="List tracks sorted by BPM with metadata")
    parser.add_argument("--tracks-in-playlists", action="store_true", help="List all tracks that are in at least one playlist")
    parser.add_argument("--debug-parse-playlist-item-blob", type=str, help="Parse a hex BLOB from mediaItemPlaylistItems for debugging")
    parser.add_argument("--extract-all-playlist-mappings", action="store_true", help="Extract and print all playlist-to-track mappings from the database")
    parser.add_argument("--debug-parse-blob-uuid", type=str, help="UUID to debug parse from database2")
    parser.add_argument("--debug-parse-blob-collection", type=str, help="Collection name for debug parse (e.g. mediaItems, mediaItemPlaylists, mediaItemPlaylistItems)")
    args = parser.parse_args()
    if args.debug_parse_playlist_item_blob:
        tracks_by_bpm = TracksByBPM(args.database_path)
        tracks_by_bpm.debug_parse_playlist_item_blob(args.debug_parse_playlist_item_blob)
        return
    if args.extract_all_playlist_mappings:
        tracks_by_bpm = TracksByBPM(args.database_path)
        tracks_by_bpm.extract_all_playlist_mappings()
        return
    if args.debug_parse_blob_uuid:
        tracks_by_bpm = TracksByBPM(args.database_path)
        tracks_by_bpm.debug_parse_blob_by_uuid(args.debug_parse_blob_uuid)
        return
    
    if not args.tracks_by_bpm_with_metadata:
        # Default behavior
        args.tracks_by_bpm_with_metadata = True
    
    tracks_by_bpm = TracksByBPM(args.database_path)
    if args.tracks_in_playlists:
        tracks_by_bpm.list_tracks_in_playlists(args.database_path, args.limit)
    elif args.tracks_by_bpm_with_metadata:
        tracks_by_bpm.list_tracks_by_bpm_with_metadata(args.limit, args.show_all_properties)
    else:
        tracks_by_bpm.list_tracks_by_bpm_with_metadata(args.limit, args.show_all_properties)


if __name__ == "__main__":
    main() 