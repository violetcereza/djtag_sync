def clean_genre_list(genre_list):
    """
    Split genre strings on commas, remove duplicates, and sort alphabetically
    """
    genre_split = [g.strip() for genre in genre_list for g in genre.split(',')]
    return sorted(set(genre_split)) 