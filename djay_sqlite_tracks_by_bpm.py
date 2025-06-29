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
        """Parse TSAF blob to extract all possible track properties."""
        properties = {}
        
        # Convert the BLOB to an ASCII string for easier parsing
        ascii_string = ""
        for byte in data:
            if 32 <= byte < 127:
                ascii_string += chr(byte)
            else:
                ascii_string += "\0"
        
        def value_before(field: str) -> Optional[str]:
            """Extract the value that comes immediately before a field name."""
            if field not in ascii_string:
                return None
            before = ascii_string[:ascii_string.index(field)]
            parts = [part for part in before.split("\0") if part.strip()]
            return parts[-1] if parts else None
        
        def extract_all_strings() -> List[str]:
            """Extract all readable strings from the blob."""
            strings = []
            current_string = ""
            for byte in data:
                if 32 <= byte < 127:
                    current_string += chr(byte)
                else:
                    if current_string.strip():
                        strings.append(current_string.strip())
                    current_string = ""
            if current_string.strip():
                strings.append(current_string.strip())
            return strings
        
        # Extract known fields
        properties['title'] = value_before("title")
        properties['artist'] = value_before("artist")
        properties['album'] = value_before("album")
        properties['genre'] = value_before("genre")
        properties['composer'] = value_before("composer")
        properties['year'] = value_before("year")
        properties['track_number'] = value_before("trackNumber")
        properties['album_track_number'] = value_before("albumTrackNumber")
        properties['disc_number'] = value_before("discNumber")
        properties['grouping'] = value_before("grouping")
        properties['comments'] = value_before("comments")
        properties['content_type'] = value_before("contentType")
        properties['file_type'] = value_before("file")
        properties['origin_source_id'] = value_before("originSourceID")
        properties['uuid'] = value_before("uuid")
        properties['title_id'] = value_before("titleID")
        properties['artist_uuids'] = value_before("artistUUIDs")
        properties['album_uuid'] = value_before("albumUUID")
        properties['genre_uuids'] = value_before("genreUUIDs")
        
        # Try to extract binary values (duration, BPM, sample rate, bit rate)
        try:
            # Look for common binary patterns
            # Duration is often stored as a 4-byte float
            for i in range(len(data) - 4):
                try:
                    duration_bytes = data[i:i+4]
                    duration_value = struct.unpack('f', duration_bytes)[0]
                    if 0 < duration_value < 36000:  # Reasonable duration range (0-10 hours)
                        properties['duration_seconds'] = duration_value
                        break
                except:
                    continue
            
            # BPM is often stored as a 4-byte float
            for i in range(len(data) - 4):
                try:
                    bpm_bytes = data[i:i+4]
                    bpm_value = struct.unpack('f', bpm_bytes)[0]
                    if 0 < bpm_value < 300:  # Reasonable BPM range
                        properties['bpm_from_blob'] = bpm_value
                        break
                except:
                    continue
            
            # Sample rate (often 44100, 48000, etc.)
            for i in range(len(data) - 4):
                try:
                    sample_rate_bytes = data[i:i+4]
                    sample_rate_value = struct.unpack('I', sample_rate_bytes)[0]
                    if sample_rate_value in [44100, 48000, 96000, 192000, 22050, 24000]:
                        properties['sample_rate'] = sample_rate_value
                        break
                except:
                    continue
            
            # Bit rate
            for i in range(len(data) - 4):
                try:
                    bit_rate_bytes = data[i:i+4]
                    bit_rate_value = struct.unpack('I', bit_rate_bytes)[0]
                    if 32000 <= bit_rate_value <= 320000:  # Reasonable bit rate range
                        properties['bit_rate'] = bit_rate_value
                        break
                except:
                    continue
                    
        except Exception as e:
            properties['binary_parse_error'] = str(e)
        
        # Extract all readable strings for analysis
        all_strings = extract_all_strings()
        properties['all_strings'] = all_strings
        
        # Look for additional patterns
        for string in all_strings:
            # Look for UUIDs (32 hex characters)
            if len(string) == 32 and all(c in '0123456789abcdef' for c in string.lower()):
                if 'uuid' not in properties:
                    properties['uuid'] = string
                elif 'additional_uuids' not in properties:
                    properties['additional_uuids'] = [string]
                else:
                    properties['additional_uuids'].append(string)
            
            # Look for years
            if string.isdigit() and 1900 <= int(string) <= 2030:
                if 'year' not in properties:
                    properties['year'] = int(string)
            
            # Look for track numbers
            if string.isdigit() and 1 <= int(string) <= 999:
                if 'track_number' not in properties:
                    properties['track_number'] = int(string)
            
            # Look for file extensions
            if string.startswith('.') and len(string) <= 5:
                properties['file_extension'] = string
        
        # Remove None values
        properties = {k: v for k, v in properties.items() if v is not None}
        
        return properties
    
    def get_playlists_for_track(self, track_key: str, cursor: sqlite3.Cursor) -> List[str]:
        """Get all playlists that contain a specific track."""
        playlists = []
        
        try:
            # First, get the track's UUID from the mediaItems collection
            cursor.execute(
                "SELECT data FROM database2 WHERE collection = 'mediaItems' AND key = ?",
                (track_key,)
            )
            result = cursor.fetchone()
            if not result or not result[0]:
                return []
            
            # Parse the track's TSAF data to get its UUID
            track_props = self.parse_tsaf_blob(result[0])
            track_uuid = track_props.get('uuid')
            if not track_uuid:
                return []
            
            # Find playlist items that reference this track UUID
            cursor.execute(
                "SELECT data FROM database2 WHERE collection = 'mediaItemPlaylistItems' AND data LIKE ?",
                (f'%{track_uuid}%',)
            )
            playlist_item_results = cursor.fetchall()
            
            for item_result in playlist_item_results:
                if item_result[0]:
                    try:
                        item_props = self.parse_tsaf_blob(item_result[0])
                        playlist_uuid = item_props.get('playlistUUID')
                        
                        if playlist_uuid:
                            # Find the playlist with this UUID
                            cursor.execute(
                                "SELECT data FROM database2 WHERE collection = 'mediaItemPlaylists' AND data LIKE ?",
                                (f'%{playlist_uuid}%',)
                            )
                            playlist_result = cursor.fetchone()
                            
                            if playlist_result and playlist_result[0]:
                                try:
                                    playlist_props = self.parse_tsaf_blob(playlist_result[0])
                                    playlist_name = playlist_props.get('name')
                                    
                                    if playlist_name:
                                        # Try to get the name from the index first
                                        cursor.execute(
                                            "SELECT name FROM secondaryIndex_mediaItemPlaylistIndex WHERE rowid = ?",
                                            (playlist_uuid,)
                                        )
                                        index_result = cursor.fetchone()
                                        
                                        if index_result and index_result[0]:
                                            playlists.append(index_result[0])
                                        else:
                                            # If not in index, use the name from TSAF
                                            playlists.append(playlist_name)
                                            
                                except Exception as e:
                                    continue
                                    
                    except Exception as e:
                        continue
            
        except sqlite3.Error as e:
            # If query fails, return empty list
            pass
        
        return list(set(playlists))  # Remove duplicates
    
    def get_track_metadata(self, rowid: int, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        """Get track metadata for a given rowid."""
        # Get the key from mediaItemAnalyzedData collection
        cursor.execute(
            "SELECT key FROM database2 WHERE rowid = ? AND collection = 'mediaItemAnalyzedData'",
            (rowid,)
        )
        result = cursor.fetchone()
        if not result:
            return {}
        
        key = result[0]
        
        # Get the corresponding mediaItems entry
        cursor.execute(
            "SELECT rowid FROM database2 WHERE collection = 'mediaItems' AND key = ?",
            (key,)
        )
        result = cursor.fetchone()
        if not result:
            return {}
        
        media_rowid = result[0]
        
        # Get the BLOB data
        cursor.execute("SELECT data FROM database2 WHERE rowid = ?", (media_rowid,))
        result = cursor.fetchone()
        if not result or not result[0]:
            return {}
        
        blob_data = result[0]
        properties = self.parse_tsaf_blob(blob_data)
        
        # Add playlist information
        playlists = self.get_playlists_for_track(key, cursor)
        if playlists:
            properties['playlists'] = playlists
        
        return properties
    
    def list_tracks_by_bpm_with_metadata(self, limit: int = 50, show_all_properties: bool = False):
        """List tracks sorted by BPM with metadata."""
        print("Tracks sorted by BPM (with metadata):")
        print("=====================================")
        
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Query tracks by BPM
            query = """
                SELECT rowid, bpm, manualBPM, keySignatureIndex 
                FROM secondaryIndex_mediaItemAnalyzedDataIndex 
                WHERE bpm IS NOT NULL 
                ORDER BY bpm 
                LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            tracks = cursor.fetchall()
            
            if not tracks:
                print("No tracks with BPM data found.")
                return
            
            track_count = 0
            for track in tracks:
                track_count += 1
                rowid, bpm, manual_bpm, key_signature_index = track
                
                # Get metadata for this track
                properties = self.get_track_metadata(rowid, cursor)
                
                print(f"{track_count}. Track rowid: {rowid}")
                print(f"   BPM: {bpm:.1f}")
                if manual_bpm and manual_bpm > 0:
                    print(f"   Manual BPM: {manual_bpm:.1f}")
                
                # Show key properties
                if properties.get('title'):
                    print(f"   Title: {properties['title']}")
                if properties.get('artist'):
                    print(f"   Artist: {properties['artist']}")
                if properties.get('album'):
                    print(f"   Album: {properties['album']}")
                if properties.get('genre'):
                    print(f"   Genre: {properties['genre']}")
                if properties.get('year'):
                    print(f"   Year: {properties['year']}")
                if properties.get('track_number'):
                    print(f"   Track Number: {properties['track_number']}")
                if properties.get('duration_seconds'):
                    print(f"   Duration: {properties['duration_seconds']:.1f}s")
                if properties.get('sample_rate'):
                    print(f"   Sample Rate: {properties['sample_rate']} Hz")
                if properties.get('bit_rate'):
                    print(f"   Bit Rate: {properties['bit_rate']} bps")
                if properties.get('playlists'):
                    print(f"   Playlists: {', '.join(properties['playlists'])}")
                
                print(f"   Key Signature Index: {key_signature_index}")
                
                # Show all properties if requested
                if show_all_properties:
                    print("   All Properties:")
                    for key, value in properties.items():
                        if key not in ['title', 'artist', 'album', 'genre', 'year', 'track_number', 'duration_seconds', 'sample_rate', 'bit_rate', 'playlists']:
                            print(f"     {key}: {value}")
                
                print()
            
            if track_count == limit:
                print(f"... showing first {limit} tracks. Use a higher limit to see more.")
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM secondaryIndex_mediaItemAnalyzedDataIndex WHERE bpm IS NOT NULL")
            total = cursor.fetchone()[0]
            print(f"Total tracks with BPM data: {total}")
            
        except sqlite3.Error as e:
            print(f"Error querying BPM data: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def list_tracks_in_playlists(self, database_path: str, limit: int = 50):
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        print("Tracks in at least one playlist:")
        print("===============================")
        count = 0
        # Get all playlist items
        cursor.execute("SELECT data FROM database2 WHERE collection = 'mediaItemPlaylistItems'")
        playlist_items = cursor.fetchall()
        track_uuid_to_playlists = {}
        for item in playlist_items:
            if not item[0]:
                continue
            try:
                item_props = self.parse_tsaf_blob(item[0])
                track_uuid = item_props.get('mediaItemUUID')
                playlist_uuid = item_props.get('playlistUUID')
                if not track_uuid or not playlist_uuid:
                    continue
                if track_uuid not in track_uuid_to_playlists:
                    track_uuid_to_playlists[track_uuid] = set()
                track_uuid_to_playlists[track_uuid].add(playlist_uuid)
            except Exception:
                continue
        # For each track UUID, get metadata and playlist names
        for track_uuid, playlist_uuids in track_uuid_to_playlists.items():
            # Find the mediaItems key for this UUID
            cursor.execute("SELECT key, data FROM database2 WHERE collection = 'mediaItems'")
            found = False
            for key, data in cursor.fetchall():
                try:
                    props = self.parse_tsaf_blob(data)
                    if props.get('uuid') == track_uuid:
                        found = True
                        break
                except Exception:
                    continue
            if not found:
                continue
            properties = props
            # Get playlist names
            playlist_names = []
            for playlist_uuid in playlist_uuids:
                cursor.execute("SELECT name FROM secondaryIndex_mediaItemPlaylistIndex WHERE rowid = ?", (playlist_uuid,))
                result = cursor.fetchone()
                if result and result[0]:
                    playlist_names.append(result[0])
                else:
                    # Fallback: get from TSAF
                    cursor.execute("SELECT data FROM database2 WHERE collection = 'mediaItemPlaylists' AND data LIKE ?", (f'%{playlist_uuid}%',))
                    playlist_result = cursor.fetchone()
                    if playlist_result and playlist_result[0]:
                        try:
                            playlist_props = self.parse_tsaf_blob(playlist_result[0])
                            if playlist_props.get('name'):
                                playlist_names.append(playlist_props['name'])
                        except Exception:
                            continue
            print(f"Track UUID: {track_uuid}")
            if properties.get('title'):
                print(f"   Title: {properties['title']}")
            if properties.get('artist'):
                print(f"   Artist: {properties['artist']}")
            print(f"   Playlists: {', '.join(playlist_names)}")
            print()
            count += 1
            if count >= limit:
                print(f"... showing first {limit} tracks. Use a higher limit to see more.")
                break
        print(f"Total tracks in playlists: {count}")


def main():
    parser = argparse.ArgumentParser(description="List tracks by BPM from djay database")
    parser.add_argument("database_path", help="Path to the djay database file")
    parser.add_argument("--limit", type=int, default=50, help="Number of tracks to show (default: 50)")
    parser.add_argument("--show-all-properties", action="store_true", 
                       help="Show all extracted properties for each track")
    parser.add_argument("--tracks-by-bpm-with-metadata", action="store_true", 
                       help="List tracks sorted by BPM with metadata")
    parser.add_argument("--tracks-in-playlists", action="store_true", help="List all tracks that are in at least one playlist")
    
    args = parser.parse_args()
    
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