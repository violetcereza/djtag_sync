#!/usr/bin/env python3
"""
DJLibrary base class for music library management.
"""

import os
import pickle
from abc import ABC, abstractmethod
from datetime import datetime
import yaml
from library_diff import DJLibraryDiff
from colorama import Style, Fore

class DJLibrary(ABC):
    
    def __init__(self, music_folder: str):
        """
        Initialize DJLibrary with a music folder path.
        
        Args:
            music_folder (str): Path to the music folder
        """
        self.music_folder = os.path.abspath(os.path.expanduser(music_folder))
        self.library_type = self.__class__.__name__
        self.tracks = self._scan()
        self.commits = self._scan_commits()
        self.meta = self._read_meta()
    
    @abstractmethod
    def _scan(self):
        """
        Abstract method to scan the library for tracks.
        Must be implemented by subclasses.
        
        Returns:
            dict: Dictionary of {file_path: Track instance}
        """
        pass
    
    @abstractmethod
    def writeLibrary(self):
        """
        Abstract method to write the library to its storage medium.
        Must be implemented by subclasses.
        """
        pass
    
    def _read_meta(self):
        """
        Read the meta.yaml file.
        """
        djtag_dir = os.path.join(self.music_folder, '.djtag', self.library_type)
        meta_path = os.path.join(djtag_dir, 'meta.yaml')
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _write_meta(self):
        """
        Write the meta.yaml file.
        """
        djtag_dir = os.path.join(self.music_folder, '.djtag', self.library_type)
        meta_path = os.path.join(djtag_dir, 'meta.yaml')
        with open(meta_path, 'w') as f:
            yaml.dump(self.meta, f)

    def _scan_commits(self):
        """
        Load the commits from pickle file.
        """
        djtag_dir = os.path.join(self.music_folder, '.djtag', self.library_type)
        commits = []
        for file in os.listdir(djtag_dir):
            if file.endswith('.pkl'):
                commits.append(self._commit_file_to_datetime(file))
        return commits
    
    def _commit_file_to_datetime(self, commit_file):
        """
        Convert a commit file name to a datetime object.
        """
        return datetime.strptime(commit_file.split('.')[0], '%Y-%m-%d_%H-%M-%S')
    
    def _datetime_to_commit_file(self, dt):
        """
        Convert a datetime object to a commit file name.
        """
        return f"{dt.strftime('%Y-%m-%d_%H-%M-%S')}.pkl"

    def load_commit(self, commit_datetime):
        """
        Load the commit from pickle file.
        """
        commit_file = self._datetime_to_commit_file(commit_datetime)
        with open(os.path.join(self.music_folder, '.djtag', self.library_type, commit_file), 'rb') as f:
            return pickle.load(f)

    def merge(self, other_library):
        """
        Merge the current library state with the other library state.
        First, check djtag_dir/meta.yaml to see when 
        {other_library.library_type: {last_merged: Date}} was.
        """

        other_type = other_library.library_type
        last_merged = self.meta.get(other_type, {}).get('last_merged')
        try:
            last_merged_dt = datetime.fromisoformat(last_merged) if last_merged else None
        except Exception:
            print(f"Could not parse last_merged date: {last_merged}")
            last_merged_dt = None

        print(
            f"{Fore.CYAN}Merging{Style.RESET_ALL} all changes on "
            f"{other_library.library_type} since last merge at {last_merged_dt}"
        )
        # Filter commits after last_merged
        filtered_commits = [
            dt for dt in other_library.commits
            if (last_merged_dt is None or dt > last_merged_dt)
        ]
        filtered_commits.sort()

        if len(filtered_commits) == 0:
            print(f"{Style.DIM}No commits on {other_library.library_type} since last merge.{Style.RESET_ALL}")
            return

        prev_commit = None
        for dt in filtered_commits:
            commit_obj = other_library.load_commit(dt)
            if prev_commit is not None:
                diff = DJLibraryDiff(prev_commit, commit_obj)
                if diff:
                    # print("\n")
                    print(diff)
                    delta = diff.delta()
                    # Apply the delta from the other library to self.tracks
                    try:
                        self.tracks += delta
                    except Exception as e:
                        print(f"Error applying changes: {e}")
            prev_commit = commit_obj

        # if not self.diff():
        #     print(f"{Style.DIM}No updates needed to {self.library_type} from {other_library.library_type}.{Style.RESET_ALL}")
        #     return

        # After applying all deltas, print the diff between the most recent commit and self.tracks
        print("Diff after applying deltas:")
        print(self.diff())

        self.writeLibrary()
        self.commit()

        if other_type not in self.meta:
            self.meta[other_type] = {}
        self.meta[other_type]['last_merged'] = datetime.now().isoformat()
        self._write_meta()

        return
   
    def diff(self):
        """
        Diff the current library state with the commit.
        """
        if not self.commits:
            raise ValueError("No commits found to diff against.")
        most_recent_commit = max(self.commits)
        commit = self.load_commit(most_recent_commit)
        diff = DJLibraryDiff(commit, self)
        return diff
 
    def commit(self):
        """
        Commit the current library state to pickle file.
        """
        if not self.diff():
            print(f"{Style.DIM}No changes detected for {self.library_type}. Commit not saved.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.CYAN}Committing{Style.RESET_ALL} {self.library_type}...")
        print(self.diff())
        djtag_dir = os.path.join(self.music_folder, '.djtag', self.library_type)
        os.makedirs(djtag_dir, exist_ok=True)
        commit_file = self._datetime_to_commit_file(datetime.now())
        filepath = os.path.join(djtag_dir, commit_file)
        with open(filepath, 'wb') as f:
            pickle.dump(self, f) 
        self.commits.append(datetime.now())