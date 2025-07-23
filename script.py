import os
import yaml
import subprocess
from datetime import datetime
import shutil
from id3 import is_music_file, scan_music_folder, write_music_folder
from swinsian import scan_swinsian_library, write_swinsian_library

# DEFAULT_SERATO = os.path.expanduser('~/Music/_Serato_/Subcrates')

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