# utils_pymongo.py

from pymongo import ASCENDING, DESCENDING

def parse_sort_criteria(sort_by: str):
    """
    Parse the sort_by string into a list of sorting criteria.

    Example:
    Input: 'field1,-field2'
    Output: [('field1', ASCENDING), ('field2', DESCENDING)]
    """
    sort_criteria = []
    if sort_by:
        for field in sort_by.split(','):
            direction = ASCENDING
            if field.startswith('-'):
                direction = DESCENDING
                field = field[1:]  # Remove the '-' prefix
            sort_criteria.append((field, direction))
    return sort_criteria

def parse_filter_criteria(filter_string: str):
    """
    Parse the filter query string into a dictionary of filter criteria.

    Example:
    Input: 'field1:value1,field2:*value2*'
    Output: {'field1': 'value1', 'field2': {'$regex': '.*value2.*'}}
    """

    filter_criteria = []
    if filter_string:
        filter_parts = filter_string.split(',')
        for part in filter_parts:
            key, value = part.split(':', maxsplit=1)
            if '*' in value:
                value = {'$regex': value.replace('*', '.*')}
            filter_criteria.append({key: value})
    return filter_criteria



def apply_sort(cursor, sort_criteria):
    """
    Apply sorting to the MongoDB cursor based on the sorting criteria.
    """
    if not sort_criteria:
            cursor = cursor.sort([("_id", DESCENDING)])
    else:
        cursor = cursor.sort(sort_criteria)
    return cursor
