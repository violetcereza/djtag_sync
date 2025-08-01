#!/usr/bin/env python3
"""
Script to create instances of SwinsianLibrary and ID3Library.
"""

from swinsian import SwinsianLibrary
from id3 import ID3Library
import os
import argparse

def main():
    parser = argparse.ArgumentParser(
        description='Sync music tags between ID3 & Swinsian libraries.')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    DEFAULT_SWINSIAN_DB = '~/Library/Application Support/Swinsian/Library.sqlite'
    DEFAULT_MUSIC_FOLDER = '~/Dropbox/Cloud Music/Testing DJ Library'
    SOURCES_CHOICES = ['id3', 'swinsian']

    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Pull and commit tags from specified library sources')
    fetch_parser.add_argument('sources', nargs='*', 
        help=f'Library sources to fetch from ({", ".join(SOURCES_CHOICES)}). If none specified, fetches all sources.')
    fetch_parser.add_argument('--swinsian-db', help='Path to Swinsian database', 
        default=DEFAULT_SWINSIAN_DB)
    fetch_parser.add_argument('--music-folder', help='Path to the music folder', 
        default=DEFAULT_MUSIC_FOLDER)
    
    # Merge command (stub)
    merge_parser = subparsers.add_parser('merge', help='Merge ID3 and Swinsian branches (not implemented)')
    merge_parser.add_argument('sources', nargs='+', choices=SOURCES_CHOICES, 
        help=f'Library sources to merge ({", ".join(SOURCES_CHOICES)})')
    merge_parser.add_argument('--swinsian-db', help='Path to Swinsian database', 
        default=DEFAULT_SWINSIAN_DB)
    merge_parser.add_argument('--music-folder', help='Path to the music folder', 
        default=DEFAULT_MUSIC_FOLDER)
    
    # Push command
    push_parser = subparsers.add_parser('push', help='Write tags back to libraries')
    push_parser.add_argument('sources', nargs='+', choices=SOURCES_CHOICES, 
        help=f'Library sources to push to ({", ".join(SOURCES_CHOICES)})')
    push_parser.add_argument('--swinsian-db', help='Path to Swinsian database', 
        default=DEFAULT_SWINSIAN_DB)
    push_parser.add_argument('--music-folder', help='Path to the music folder', 
        default=DEFAULT_MUSIC_FOLDER)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    library_dir = os.path.expanduser(args.music_folder)
    djtag_dir = os.path.join(library_dir, '.djtag')
    if args.command == 'fetch':
        print(f"Fetch command not implemented yet for sources: {', '.join(args.sources)}")
    elif args.command == 'merge':

        swinsian = SwinsianLibrary(args.swinsian_db)
        id3 = ID3Library(args.music_folder)
        for path in set(swinsian.tracks.keys()) & set(id3.tracks.keys()):
            s_track = swinsian.tracks[path]
            i_track = id3.tracks[path]
            diff = s_track.diff(i_track)
            print(f"Diff for {path}: {diff}")
        
    elif args.command == 'push':
        print(f"Push command not implemented yet for sources: {', '.join(args.sources)}")

if __name__ == '__main__':
    main() 