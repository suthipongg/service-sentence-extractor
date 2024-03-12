def extract_serializer(extract) -> dict:
    return {
        'id':str(extract["_id"]),
        'created_at':extract["created_at"],
        'sentence':extract["sentence"],
        # 'sentence_vector':extract["sentence_vector"],
        'counter':extract["counter"],
    }


def extracts_serializer(extracts) -> list:
    return [extract_serializer(extract) for extract in extracts]
