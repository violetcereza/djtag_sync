# djtag API

- djtag fetch
    - Writes the library contents to yaml files in the .djtag directory, and commits the changes on the associated branch
- djtag merge
    - Unifies all the data sources onto the id3 branch, using git on the yaml file commits
- djtag push
    - Writes the yaml state on the id3 branch to a DJ library
- djtag sync
    - Runs fetch, merge, then push

# Merge case study

- Added to swinsian playlist
    - Add to id3 tags
- Removed from swinsian playlist
    - Remove from id3 tags
- Added id3 genre
    - Add to swinsian playlist
- Removed id3 genre
    - Remove from swinsian playlist
- Removed from swinsian playlist, additional id3 tags added
    - Add to swinsian playlist, remove tags
- Add new file to id3 library
    - Add id3 tracker file, don't add swinsian file
- Add new file to swinsian library
    - Add swinisian tracker if file is in id3 folder
- Track new field in id3
    - Don't add data to swinsian branch when merging
    - 

# TODO: Internal data structure

- Track
    - path
        extension shouldn't be changable! its a different file
    - tags
- Library
    - read and write methods