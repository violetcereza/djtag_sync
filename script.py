import os
import yaml
import subprocess
from datetime import datetime
import shutil
from id3 import is_music_file, scan_music_folder, write_music_folder
from swinsian import scan_swinsian_library, write_swinsian_library

# DEFAULT_SERATO = os.path.expanduser('~/Music/_Serato_/Subcrates')

def scan_yaml(djtag_dir):
    """
    Scans the .djtag folder for YAML files and returns a dict:
    {file_path: tags}
    """
    yaml_tracks = {}
    for root, _, files in os.walk(djtag_dir):
        for file in files:
            if file.endswith('.yaml'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    tags = yaml.load(f, Loader=yaml.SafeLoader)
                yaml_tracks[tags['path'][0]] = tags
    return yaml_tracks


def write_yaml(tracks, djtag_dir):
    """
    Writes YAML files for each file_path in tracks.
    """
    # Delete all files in djtag_dir except .gitignore
    print("Resetting .djtag folder...")
    for file in os.listdir(djtag_dir):
        if file != '.gitignore' and file != '.git':
            path = os.path.join(djtag_dir, file)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
    
    library_dir = os.path.abspath(os.path.join(djtag_dir, '..'))
    for file_path, tags in tracks.items():
        if not os.path.commonpath([os.path.abspath(file_path), os.path.abspath(library_dir)]) == \
            os.path.abspath(library_dir):
            print(f"Skipping {file_path} because it's not in the library directory")
            continue

        rel_path = os.path.relpath(file_path, library_dir)
        base_name, _ = os.path.splitext(rel_path)
        yaml_path = os.path.join(djtag_dir, f'{base_name}.yaml')
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
        # Default to all sources if none specified
        sources = args.sources if args.sources else SOURCES_CHOICES
        
        # Validate sources
        invalid_sources = [s for s in sources if s not in SOURCES_CHOICES]
        if invalid_sources:
            print(f"Error: Invalid sources: {', '.join(invalid_sources)}")
            print(f"Valid sources are: {', '.join(SOURCES_CHOICES)}")
            return
        
        print(f"Fetching tags from: {', '.join(sources)}")
        
        if 'id3' in sources:
            print("Pulling tags from ID3...")
            id3_tracks = scan_music_folder(library_dir)
            write_yaml(id3_tracks, djtag_dir)
            print("Committing ID3 tags to git...")
            commit_yaml_to_git(djtag_dir, 'id3')
        
        if 'swinsian' in sources:
            print("Pulling tags from Swinsian...")
            swinsian_db = os.path.expanduser(args.swinsian_db)
            swinsian_tracks = scan_swinsian_library(swinsian_db)
            write_yaml(swinsian_tracks, djtag_dir)
            print("Committing Swinsian tags to git...")
            commit_yaml_to_git(djtag_dir, 'swinsian')
        
    elif args.command == 'merge':
        print(f"Merge command not implemented yet for sources: {', '.join(args.sources)}")
        # TODO: Implement merge functionality
        # This should merge the specified source branches
        
    elif args.command == 'push':
        print(f"Pushing tags to: {', '.join(args.sources)}")
        
        # Scan merged YAML files
        print("Scanning merged YAML files...")
        yaml_tracks = scan_yaml(djtag_dir)
        
        if 'swinsian' in args.sources:
            # Write to Swinsian library
            print("Writing Swinsian library...")
            swinsian_db = os.path.expanduser(args.swinsian_db)
            write_swinsian_library(yaml_tracks, swinsian_db)
        
        if 'id3' in args.sources:
            # Write to ID3 tags
            print("Writing ID3 tags in music folder...")
            write_music_folder(yaml_tracks, library_dir)

if __name__ == '__main__':
    main() 