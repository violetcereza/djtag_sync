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
        for track in self.tracks.values():
            self._scaffold_track(track, None)
    
    @abstractmethod
    def _scan(self):
        """
        Abstract method to scan the library for tracks.
        Must be implemented by subclasses.
        
        Returns:
            dict: Dictionary of {file_path: Track instance}
        """
        print(f"{Fore.CYAN}Scanning{Style.RESET_ALL} {self.library_type}")
    
    @abstractmethod
    def writeLibrary(self):
        """
        Abstract method to write the library to its storage medium.
        Must be implemented by subclasses.
        """
        print(f"{Fore.CYAN}Writing{Style.RESET_ALL} {self.library_type}")
    
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

    def commit(self):
        """
        Commit the current library state to pickle file.
        """
        if not self.diff():
            print(f"{Style.DIM}Skipping redundant commit for {self.library_type}.{Style.RESET_ALL}")
            return
        
        djtag_dir = os.path.join(self.music_folder, '.djtag', self.library_type)
        os.makedirs(djtag_dir, exist_ok=True)
        commit_file = self._datetime_to_commit_file(datetime.now())
        filepath = os.path.join(djtag_dir, commit_file)
        print(f"{Fore.CYAN}Committing{Style.RESET_ALL} {self.library_type} to {commit_file}")
        print(self.diff())
        with open(filepath, 'wb') as f:
            pickle.dump(self, f) 
        self.commits.append(datetime.now())
    
    def load_commit(self, commit_datetime):
        """
        Load the commit from pickle file.
        """
        commit_file = self._datetime_to_commit_file(commit_datetime)
        with open(os.path.join(self.music_folder, '.djtag', self.library_type, commit_file), 'rb') as f:
            return pickle.load(f)

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
    
    def apply(self, diff: DJLibraryDiff):
        """
        Apply a DJLibraryDiff to this library, modifying the tracks in place.
        Uses library-specific scaffolding to ensure consistent state.
        
        Args:
            diff (DJLibraryDiff): The diff to apply to this library
        """
        for file_path, diff_info in diff.diffs.items():
            if diff_info['type'] == 'modified':
                diff_obj = diff_info['diff']
                
                # Get the target track (should exist since we're only processing modified tracks)
                if file_path in self.tracks:
                    target_track = self.tracks[file_path]
                    
                    # Apply the diff using the track's apply method
                    target_track.apply(diff_obj)
                    
                    # Apply library-specific scaffolding after the diff
                    self._scaffold_track(target_track, diff_obj)
 
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
            f"{Fore.CYAN}Merging{Style.RESET_ALL} changes from "
            f"{other_library.library_type} to {self.library_type} {Style.DIM}since last merge at {last_merged_dt}{Style.RESET_ALL}"
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

        # Load the last commit before the filtered commits
        prev_commit = other_library.load_commit(
            max((dt for dt in other_library.commits if dt < filtered_commits[0]), default=None)
        )
        for dt in filtered_commits:
            commit_obj = other_library.load_commit(dt)
            diff = DJLibraryDiff(prev_commit, commit_obj)
            if diff:
                print(f"{Style.DIM}Applying diff from {dt}{Style.RESET_ALL}")
                print(diff)
                self.apply(diff)
            prev_commit = commit_obj

        if not self.diff():
            print(f"{Style.DIM}No updates needed to {self.library_type} from {other_library.library_type}.{Style.RESET_ALL}")
        else:
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
    
    def _scaffold_track(self, track, diff_obj):
        """
        Scaffold the track to ensure library consistency.
        This is called after applying the diff to clean up the track state.
        
        Args:
            track (Track): The track to scaffold
            diff_obj (DeepDiff): The diff object that was applied
        """
        # Default implementation: clean up genre tags
        if 'genre' in track.tags:
            track.tags['genre'] = self._clean_genre_list(track.tags['genre'])
    
    def _clean_genre_list(self, genre_list):
        """
        Split genre strings on commas, remove duplicates, and sort alphabetically.
        This is inherited by all DJLibrary subclasses.
        
        Args:
            genre_list: List of genre strings
            
        Returns:
            list: Cleaned and sorted genre list
        """
        genre_split = [g.strip() for genre in genre_list for g in genre.split(',')]
        return set(genre_split)
   