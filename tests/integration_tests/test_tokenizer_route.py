def test_tokenizer_counter_success(client, valid_auth_token):
    response = client.post(
        "/tokenizer/counter",
        json={"sentences": ["This is a test sentence.", "Another one!"]},
        headers={"Authorization": valid_auth_token},
    )
    assert response.status_code == 200
    assert response.json() == {"success": True, "token_count": [8, 5]}

def test_tokenizer_counter_unauthorized(client):
    response = client.post(
        "/tokenizer/counter",
        json={"sentences": ["This should fail."]},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Bearer token missing or unknown"}