#!/usr/bin/env python3
"""
DJLibraryDiff class for comparing two DJ library instances.
"""

from deepdiff import DeepDiff, Delta

class DJLibraryDiff(DeepDiff):
    """
    A class that compares two DJ library instances and extends DeepDiff.
    """
    
    def __init__(self, old_library, new_library):
        """
        Initialize DJLibraryDiff with two library instances.
        
        Args:
            old_dj_library (DJLibrary): The old/previous library state
            new_dj_library (DJLibrary): The new/current library state
        """

        from library import DJLibrary
        if not isinstance(old_library, DJLibrary) or not isinstance(new_library, DJLibrary):
            raise TypeError("Both arguments must be instances of DJLibrary.")
        
        super().__init__(
            old_library.tracks,
            new_library.tracks,
            ignore_order=True,
            report_repetition=True,
            view='tree'
        )
    
    def delta(self):
        """
        Return the deltas of the diff.
        """
        return Delta(self)

    def __str__(self):
        tracks = {}
        for action_type, actions_list in self.items():

            if action_type == 'values_changed':
                action_str = "[CHANGED] "
            elif action_type == 'dictionary_item_added':
                action_str = "[ADDED] "
            elif action_type == 'dictionary_item_removed':
                action_str = "[REMOVED] "
            elif action_type == 'iterable_item_added':
                action_str = "[ITERABLE_ADDED] "
            elif action_type == 'iterable_item_removed':
                action_str = "[ITERABLE_REMOVED] "

            for action_tree in actions_list:
                track_path = action_tree.all_up.down.t1.path

                if action_type == 'values_changed':
                    action_str += f"-{action_tree.t1}+{action_tree.t2} "
                elif action_type == 'dictionary_item_added':
                    action_str += f"+{action_tree.t2} "
                elif action_type == 'dictionary_item_removed':
                    action_str += f"-{action_tree.t1} "
                elif action_type == 'iterable_item_added':
                    action_str += f"+{action_tree.t2} "
                elif action_type == 'iterable_item_removed':
                    action_str += f"-{action_tree.t1} "
                
                if track_path not in tracks:
                    tracks[track_path] = ""

            tracks[track_path] += action_str
        
        if len(tracks) == 0:
            return "No changes"
        else:
            return str(tracks)

