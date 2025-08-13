#!/usr/bin/env python3
"""
Script to create instances of SwinsianLibrary and ID3Library.
"""

from library_swinsian import SwinsianLibrary
from library_id3 import ID3Library
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='Sync music tags between ID3 & Swinsian libraries.')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    DEFAULT_SWINSIAN_DB = '~/Library/Application Support/Swinsian/Library.sqlite'
    DEFAULT_MUSIC_FOLDER = '~/Dropbox/Cloud Music/Testing DJ Library'

    # Helper to add common arguments to subparsers
    def add_common_args(parser):
        parser.add_argument('--swinsian-db', help='Path to Swinsian database', 
            default=DEFAULT_SWINSIAN_DB)
        parser.add_argument('--music-folder', help='Path to the music folder', 
            default=DEFAULT_MUSIC_FOLDER)
    SOURCES_CHOICES = ['swinsian', 'id3']

    # Commit command
    commit_parser = subparsers.add_parser('commit', help='Pull and commit tags from specified library sources')
    commit_parser.add_argument('sources', nargs='*', 
        help=f'Library sources to fetch from ({", ".join(SOURCES_CHOICES)}). If none specified, commits all sources.')
    add_common_args(commit_parser)
    
    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Merge changes between library sources')
    merge_parser.add_argument('sources', nargs='*', 
        help=f'Library sources to merge ({", ".join(SOURCES_CHOICES)}). If none specified, merges all sources.')
    add_common_args(merge_parser)
    
    # Overwrite command
    overwrite_parser = subparsers.add_parser('overwrite', help='Overwrite tags in one library with tags from another')
    overwrite_parser.add_argument('sources', nargs=2, 
        help=f'Library sources to push to ({", ".join(SOURCES_CHOICES)})')
    add_common_args(overwrite_parser)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if not args.sources:
        args.sources = SOURCES_CHOICES

    # Transform the sources array in place to library instances
    libraries = []
    for src in args.sources:
        if src == "swinsian":
            libraries.append(SwinsianLibrary(args.music_folder, args.swinsian_db))
        elif src == "id3":
            libraries.append(ID3Library(args.music_folder))
        else:
            raise ValueError(f"Unknown source: {src}")

    # Always commit before doing anything else
    if args.command in ['commit', 'merge', 'overwrite']:
        for source in libraries:
            source.commit()

    if args.command == 'merge':
        for library_a in libraries:
            for library_b in libraries:
                if library_a != library_b:
                    library_a.merge(library_b)
        
    if args.command == 'overwrite':
        if input(f"Are you sure you want to overwrite {args.sources[0]} with {args.sources[1]}? (y/N): ").strip().lower() != 'y':
            print("Aborted overwrite.")
            return
        
        libraries[0].tracks.update(libraries[1].tracks)
        libraries[0].writeLibrary()
        libraries[0].commit()

if __name__ == '__main__':
    main() 