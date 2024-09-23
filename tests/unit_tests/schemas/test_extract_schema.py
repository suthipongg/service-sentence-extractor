import pytest

from schemas.extract_schema import extract_serializer, extract_serializer_list

@pytest.mark.parametrize(
    'extract, expected_result', 
    [
        (
            {}, 
            {}
        ),
        (
            {'_id': 1, 'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42},
            {'id': '1', 'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42}
        ),
        (
            {'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42},
            {'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42}
        ),
        (
            {'_id': 1, 'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42, 'extra_field': 'this should be ignored'},
            {'id': '1', 'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42}
        ),
        (
            None,
            {}
        )
    ]
)
def test_extract_serializer(extract, expected_result):
    result = extract_serializer(extract)
    assert result == expected_result


@pytest.mark.parametrize(
    'extracts, expected_result', 
    [
        (
            [], 
            []
        ),
        (
            [
                {'_id': 1, 'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42}
            ], 
            [
                {'id': '1', 'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42}
            ]
        ),
        (
            [
                {'_id': 1, 'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42}, 
                {'_id': 2, 'created_at': '2023-09-06', 'sentence': 'Test sentence 2', 'counter': 43}], 
            [
                {'id': '1', 'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42}, 
                {'id': '2', 'created_at': '2023-09-06', 'sentence': 'Test sentence 2', 'counter': 43}
            ]
        ),
        (
            [
                {'_id': 1, 'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42, 'extra_field': 'this should be ignored'}, 
                {'_id': 2, 'created_at': '2023-09-06', 'sentence': 'Test sentence 2', 'counter': 43, 'extra_field': 'this should be ignored'}
            ], 
            [
                {'id': '1', 'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42}, 
                {'id': '2', 'created_at': '2023-09-06', 'sentence': 'Test sentence 2', 'counter': 43}
            ]
        ),
        ( 
            [
                {'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42, 'extra_field': 'this should be ignored'}, 
                {'created_at': '2023-09-06', 'sentence': 'Test sentence 2', 'counter': 43, 'extra_field': 'this should be ignored'}
            ], 
            [
                {'created_at': '2023-09-05', 'sentence': 'Test sentence', 'counter': 42}, 
                {'created_at': '2023-09-06', 'sentence': 'Test sentence 2', 'counter': 43}
            ]
        )
    ]
)
def test_extracts_serializer(extracts, expected_result):
    result = extract_serializer_list(extracts)

    assert result == expected_result