import os
from mutagen.easyid3 import EasyID3
from mutagen.id3._util import ID3NoHeaderError
import yaml

MUSIC_EXTENSIONS = ['.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac']

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
    id3_data = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if is_music_file(file):
                file_path = os.path.join(root, file)
                try:
                    tags = EasyID3(file_path)
                    tag_dict = dict(tags)
                    id3_data.append({'file': file_path, 'tags': tag_dict})
                    save_tags_yaml(folder_path, file_path, tag_dict)
                except ID3NoHeaderError:
                    id3_data.append({'file': file_path, 'tags': {}})
                    save_tags_yaml(folder_path, file_path, {})
                except Exception as e:
                    id3_data.append({'file': file_path, 'error': str(e)})
    return id3_data

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scan a folder for music files and aggregate ID3 data.')
    parser.add_argument('folder', help='Path to the folder to scan')
    args = parser.parse_args()
    results = scan_music_folder(args.folder)
    for entry in results:
        print(f"File: {entry['file']}")
        if 'tags' in entry:
            for tag, value in entry['tags'].items():
                print(f"  {tag}: {value}")
        if 'error' in entry:
            print(f"  Error: {entry['error']}")
        print()

if __name__ == '__main__':
    main() 