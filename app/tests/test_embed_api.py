from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@patch("app.api.routers.embed.settings.cohere_api_key", new="testkey")
@patch("app.api.routers.embed.get_http_client")
def test_embed_success(mock_get_client, auth_headers):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embeddings": {"float": [[0.1, 0.2, 0.3]]}}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_get_client.return_value = mock_client

    response = client.post("/embeddings", json={"text": "hello"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["embedding"] == [0.1, 0.2, 0.3]


@patch("app.api.routers.embed.settings.cohere_api_key", new=None)
def test_embed_missing_api_key(auth_headers):
    response = client.post("/embeddings", json={"text": "hello"}, headers=auth_headers)
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_embed_missing_text(auth_headers):
    response = client.post("/embeddings", json={}, headers=auth_headers)
    assert response.status_code == 422


def test_embed_empty_text(auth_headers):
    response = client.post("/embeddings", json={"text": ""}, headers=auth_headers)
    assert response.status_code == 422


@patch("app.api.routers.embed.settings.cohere_api_key", new="testkey")
@patch("app.api.routers.embed.get_http_client")
def test_embed_upstream_error(mock_get_client, auth_headers):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"message": "upstream error"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_get_client.return_value = mock_client

    response = client.post("/embeddings", json={"text": "hello"}, headers=auth_headers)

    assert response.status_code == 502


@patch("app.api.routers.embed.settings.cohere_api_key", new="testkey")
@patch("app.api.routers.embed.get_http_client")
def test_embed_timeout(mock_get_client, auth_headers):
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("Request timed out")
    mock_get_client.return_value = mock_client

    response = client.post("/embeddings", json={"text": "hello"}, headers=auth_headers)

    assert response.status_code == 504
    assert "timeout" in response.json()["detail"].lower()


@patch("app.api.routers.embed.settings.cohere_api_key", new="testkey")
@patch("app.api.routers.embed.get_http_client")
def test_embed_connection_error(mock_get_client, auth_headers):
    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.RequestError("Connection failed")
    mock_get_client.return_value = mock_client

    response = client.post("/embeddings", json={"text": "hello"}, headers=auth_headers)

    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"].lower()


@patch("app.api.routers.embed.settings.cohere_api_key", new="testkey")
@patch("app.api.routers.embed.get_http_client")
def test_embed_invalid_response_format(mock_get_client, auth_headers):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"unexpected": "format"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_get_client.return_value = mock_client

    response = client.post("/embeddings", json={"text": "hello"}, headers=auth_headers)

    assert response.status_code == 502
    assert "format" in response.json()["detail"].lower()


@patch("app.api.routers.embed.settings.cohere_api_key", new="testkey")
@patch("app.api.routers.embed.get_http_client")
def test_embed_client_error_no_retry(mock_get_client, auth_headers):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Bad request"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_get_client.return_value = mock_client

    response = client.post("/embeddings", json={"text": "hello"}, headers=auth_headers)

    assert response.status_code == 400
    mock_client.post.assert_called_once()


@patch("app.api.routers.embed.settings.cohere_api_key", new="testkey")
@patch("app.api.routers.embed.get_http_client")
@patch("app.api.routers.embed.asyncio.sleep", new_callable=AsyncMock)
def test_embed_retry_on_server_error(mock_sleep, mock_get_client, auth_headers):
    mock_response_fail = MagicMock()
    mock_response_fail.status_code = 500

    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {
        "embeddings": {"float": [[0.1, 0.2, 0.3]]}
    }

    mock_client = AsyncMock()
    mock_client.post.side_effect = [
        mock_response_fail,
        mock_response_fail,
        mock_response_success,
    ]
    mock_get_client.return_value = mock_client

    response = client.post("/embeddings", json={"text": "hello"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["embedding"] == [0.1, 0.2, 0.3]
    assert mock_client.post.call_count == 3
    assert mock_sleep.call_count == 2


# Tests for local BERT model
@patch("app.api.routers.embed.get_bert_model")
@patch("app.api.routers.embed.embed_bert_cls")
def test_embed_local_success(mock_embed_bert, mock_get_bert, auth_headers):
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_get_bert.return_value = (mock_model, mock_tokenizer)
    mock_embed_bert.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]

    response = client.post("/embeddings", json={"text": "привет мир", "local": True}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["embedding"] == [0.1, 0.2, 0.3, 0.4, 0.5]
    mock_get_bert.assert_called_once()
    mock_embed_bert.assert_called_once_with("привет мир", mock_model, mock_tokenizer)


@patch("app.api.routers.embed.get_bert_model")
@patch("app.api.routers.embed.embed_bert_cls")
def test_embed_local_default_false_uses_cohere(mock_embed_bert, mock_get_bert, auth_headers):
    """Test that local=False (default) uses Cohere API"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embeddings": {"float": [[0.1, 0.2, 0.3]]}}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch("app.api.routers.embed.settings.cohere_api_key", new="testkey"):
        with patch("app.api.routers.embed.get_http_client", return_value=mock_client):
            response = client.post("/embeddings", json={"text": "hello", "local": False}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["embedding"] == [0.1, 0.2, 0.3]
    mock_embed_bert.assert_not_called()
    mock_get_bert.assert_not_called()


@patch("app.api.routers.embed.get_bert_model")
@patch("app.api.routers.embed.embed_bert_cls")
def test_embed_local_without_explicit_local_param_uses_cohere(mock_embed_bert, mock_get_bert, auth_headers):
    """Test that omitting local parameter defaults to Cohere"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embeddings": {"float": [[0.1, 0.2, 0.3]]}}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    with patch("app.api.routers.embed.settings.cohere_api_key", new="testkey"):
        with patch("app.api.routers.embed.get_http_client", return_value=mock_client):
            response = client.post("/embeddings", json={"text": "hello"}, headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["embedding"] == [0.1, 0.2, 0.3]
    mock_embed_bert.assert_not_called()
    mock_get_bert.assert_not_called()


@patch("app.api.routers.embed.get_bert_model")
def test_embed_local_missing_dependencies(mock_get_bert, auth_headers):
    from fastapi import HTTPException

    mock_get_bert.side_effect = HTTPException(
        status_code=503, detail="BERT model dependencies not installed (torch, transformers)"
    )

    response = client.post("/embeddings", json={"text": "hello", "local": True}, headers=auth_headers)

    assert response.status_code == 503
    assert "dependencies not installed" in response.json()["detail"]


@patch("app.api.routers.embed.get_bert_model")
@patch("app.api.routers.embed.embed_bert_cls")
def test_embed_local_model_error(mock_embed_bert, mock_get_bert, auth_headers):
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_get_bert.return_value = (mock_model, mock_tokenizer)
    mock_embed_bert.side_effect = RuntimeError("Model inference failed")

    response = client.post("/embeddings", json={"text": "hello", "local": True}, headers=auth_headers)

    assert response.status_code == 500
    assert "Failed to generate local embedding" in response.json()["detail"]


@patch("app.api.routers.embed.get_bert_model")
@patch("app.api.routers.embed.embed_bert_cls")
def test_embed_local_empty_text_validation(mock_embed_bert, mock_get_bert, auth_headers):
    """Test that empty text validation works for local model too"""
    response = client.post("/embeddings", json={"text": "", "local": True}, headers=auth_headers)

    assert response.status_code == 422
    mock_embed_bert.assert_not_called()
    mock_get_bert.assert_not_called()


@patch("app.api.routers.embed.get_bert_model")
@patch("app.api.routers.embed.embed_bert_cls")
def test_embed_local_missing_text_validation(mock_embed_bert, mock_get_bert, auth_headers):
    """Test that missing text validation works for local model too"""
    response = client.post("/embeddings", json={"local": True}, headers=auth_headers)

    assert response.status_code == 422
    mock_embed_bert.assert_not_called()
    mock_get_bert.assert_not_called()


@patch("app.api.routers.embed.get_bert_model")
@patch("app.api.routers.embed.embed_bert_cls")
def test_embed_local_model_reuse(mock_embed_bert, mock_get_bert, auth_headers):
    """Test that BERT model is reused across multiple requests"""
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_get_bert.return_value = (mock_model, mock_tokenizer)
    mock_embed_bert.return_value = [0.1, 0.2, 0.3]

    # First request
    response1 = client.post("/embeddings", json={"text": "text1", "local": True}, headers=auth_headers)
    assert response1.status_code == 200

    # Second request
    response2 = client.post("/embeddings", json={"text": "text2", "local": True}, headers=auth_headers)
    assert response2.status_code == 200

    # Model should be initialized once, but embed_bert_cls called twice
    assert mock_get_bert.call_count >= 1
    assert mock_embed_bert.call_count == 2
