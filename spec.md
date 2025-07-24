# djtag API

- djtag fetch
    - Writes the library contents to yaml files in the .djtag directory, and commits the changes on the associated branch
- djtag merge
    - Unifies all the data sources onto the id3 branch, using git on the yaml file commits
- djtag push
    - Writes the yaml state on the id3 branch to a DJ library
- djtag sync
    - Runs fetch, merge, then push

# TODO: Internal data structure

- Track
    - path
    - tags
- Library
    - read and write methods