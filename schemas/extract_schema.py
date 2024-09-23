def extract_serializer(extract) -> dict:
    if not extract:
        return {}
    result = {'id':str(extract.pop('_id'))} if '_id' in extract else {}
    for field in ['sentence', 'created_at', 'counter']:
        if field in extract:
            result[field] = extract[field]
    return result


def extract_serializer_list(extracts) -> list:
    return list(map(extract_serializer, extracts))