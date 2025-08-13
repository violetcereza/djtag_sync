#!/usr/bin/env python3
"""
DJLibraryDiff class for comparing two DJ library instances.
"""

from colorama import Fore, Style

class DJLibraryDiff:
    """
    A class that compares two DJ library instances using track-by-track comparison.
    """
    
    def __init__(self, old_library, new_library):
        """
        Initialize DJLibraryDiff with two library instances.
        
        Args:
            old_library (DJLibrary): The old/previous library state
            new_library (DJLibrary): The new/current library state
        """
        
        # Compute track-by-track differences between the two libraries
        diffs = {}
        
        # Get all unique file paths from both libraries
        all_paths = set(old_library.tracks.keys()) | set(new_library.tracks.keys())
        
        for file_path in all_paths:
            old_track = old_library.tracks.get(file_path)
            new_track = new_library.tracks.get(file_path)
            
            if old_track is None:
                # Track was added - ignore for diff purposes
                pass
            elif new_track is None:
                # Track was removed - ignore for diff purposes
                pass
            else:
                # Track exists in both, compare tags
                track_diff = old_track.diff(new_track)
                if track_diff:
                    diffs[file_path] = {
                        'type': 'modified',
                        'old_track': old_track,
                        'new_track': new_track,
                        'diff': track_diff
                    }
        
        self.diffs = diffs
        
    def __str__(self):
        """
        Return a human-readable string representation of the differences.
        """
        if not self.diffs:
            return f"{Style.DIM}No changes detected{Style.RESET_ALL}"
        
        lines = []
        modified = {path: info for path, info in self.diffs.items() if info['type'] == 'modified'}
        lines.append(f"{Style.DIM}Library changes ({len(modified)}){Style.RESET_ALL}")
        
        for path, modification in modified.items():
            diff = modification['diff']
            
            # Build the change string in the format: // -<genre removed> +<genre added> ~<other changes>
            added = []
            removed = []
            changed = []
            
            # Handle genre additions
            if 'iterable_item_added' in diff:
                for change_path, added_value in diff['iterable_item_added'].items():
                    if "root['genre']" in change_path:
                        added.append(added_value)
                    else:
                        added.append(f"{change_path}/{added_value}")
            # Handle genre removals
            if 'iterable_item_removed' in diff:
                for change_path, removed_value in diff['iterable_item_removed'].items():
                    if "root['genre']" in change_path:
                        removed.append(removed_value)
                    else:
                        removed.append(f"{change_path}/{removed_value}")
            # Handle genre additions
            if 'set_item_added' in diff:
                for change_path in diff['set_item_added']:
                    # change_path is a string like "root['genre']['test playlist']"
                    if change_path.startswith("root['genre']"):
                        # Extract the genre name between the last pair of brackets
                        # e.g., "root['genre']['test playlist']" -> "test playlist"
                        genre = change_path.split("['genre']")[-1][2:-2]
                        added.append(genre)
                    else:
                        added.append(change_path)
            # Handle genre removals
            if 'set_item_removed' in diff:
                for change_path in diff['set_item_removed']:
                    if change_path.startswith("root['genre']"):
                        genre = change_path.split("['genre']")[-1][2:-2]
                        removed.append(genre)
                    else:
                        removed.append(change_path)

            # Handle other changes
            if 'dictionary_item_added' in diff:
                for added_key in diff['dictionary_item_added']:
                    added.append(added_key)
            if 'dictionary_item_removed' in diff:
                for removed_key in diff['dictionary_item_removed']:
                    removed.append(removed_key)
            if 'values_changed' in diff:
                for changed_key, changed_value in diff['values_changed'].items():
                    if changed_key == 'root':
                        changed.append("replaced all tags")
                    else:
                        changed.append(f"{changed_key}/{changed_value}")
            
            track_str = str(modification['old_track'])
            change_str = (
                Fore.GREEN + ' '.join(f'+{item}' for item in added) + Style.RESET_ALL +
                Fore.RED + ' '.join(f'-{item}' for item in removed) + Style.RESET_ALL +
                Fore.YELLOW + ' '.join(f'~{item}' for item in changed) + Style.RESET_ALL
            )
            lines.append(f"  ♫ {track_str} {Style.DIM}//{Style.RESET_ALL} {change_str}")
        
        return "\n".join(lines)
    
    def __bool__(self):
        return bool(self.diffs)