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
            track_str = str(modification['old_track'])
            changes = []
            
            diff = modification['diff']
            
            # Build the change string in the format: // -<genre removed> +<genre added> ~<other changes>
            change_parts = []
            
            # Handle genre removals
            if 'iterable_item_removed' in diff:
                for change_path, removed_value in diff['iterable_item_removed'].items():
                    if "root['genre']" in change_path:
                        change_parts.append(f"{Fore.RED}-{removed_value}{Style.RESET_ALL}")
                    else:
                        change_parts.append(f"{Fore.RED}-{change_path}/{removed_value}{Style.RESET_ALL}")
            
            # Handle genre additions
            if 'iterable_item_added' in diff:
                for change_path, added_value in diff['iterable_item_added'].items():
                    if "root['genre']" in change_path:
                        change_parts.append(f"{Fore.GREEN}+{added_value}{Style.RESET_ALL}")
                    else:
                        change_parts.append(f"{Fore.GREEN}+{change_path}/{added_value}{Style.RESET_ALL}")
            
            # Handle other changes
            if 'dictionary_item_added' in diff:
                for added_key in diff['dictionary_item_added']:
                    change_parts.append(f"{Fore.GREEN}+{added_key}{Style.RESET_ALL}")
            if 'dictionary_item_removed' in diff:
                for removed_key in diff['dictionary_item_removed']:
                    change_parts.append(f"{Fore.RED}-{removed_key}{Style.RESET_ALL}")
            if 'values_changed' in diff:
                for changed_key, changed_value in diff['values_changed'].items():
                    if changed_key == 'root':
                        change_parts.append(f"{Fore.YELLOW}~replaced all tags{Style.RESET_ALL}")
                    else:
                        change_parts.append(f"{Fore.YELLOW}~{changed_key}/{changed_value}{Style.RESET_ALL}")
            
            lines.append(f"  ♫ {track_str} {Style.DIM}//{Style.RESET_ALL} {' '.join(change_parts)}")
        
        return "\n".join(lines)
    
    def __bool__(self):
        return bool(self.diffs)