from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _seed_vectors(metric: str = "cosine", auth_headers=None) -> tuple[str, str, str]:
    r = client.post("/libraries/", json={"name": f"lib-{metric}"}, headers=auth_headers)
    lib_id = r.json()["id"]
    r = client.post(f"/libraries/{lib_id}/documents", json={"title": "doc"}, headers=auth_headers)
    doc_id = r.json()["id"]
    r = client.post(
        f"/libraries/{lib_id}/chunks",
        json={"document_id": doc_id, "text": "a", "embedding": [0.0, 1.0, 0.0]},
        headers=auth_headers,
    )
    c1 = r.json()["id"]
    r = client.post(
        f"/libraries/{lib_id}/chunks",
        json={"document_id": doc_id, "text": "b", "embedding": [1.0, 0.0, 0.0]},
        headers=auth_headers,
    )
    c2 = r.json()["id"]
    return lib_id, c1, c2


def test_build_index_validations(auth_headers):
    lib_id, _, _ = _seed_vectors("cosine", auth_headers)

    # valid: linear+cosine
    r = client.put(
        f"/libraries/{lib_id}/index", json={"algorithm": "linear", "metric": "cosine"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["algorithm"] == "linear"
    assert r.json()["metric"] == "cosine"

    # invalid combinations
    r = client.put(
        f"/libraries/{lib_id}/index", json={"algorithm": "kdtree", "metric": "cosine"}, headers=auth_headers
    )
    assert r.status_code == 400

    r = client.put(
        f"/libraries/{lib_id}/index", json={"algorithm": "lsh", "metric": "euclidean"}, headers=auth_headers
    )
    assert r.status_code == 400

    r = client.put(
        f"/libraries/{lib_id}/index", json={"algorithm": "unknown", "metric": "cosine"}, headers=auth_headers
    )
    assert r.status_code == 400


def test_search_without_built_index_falls_back_and_respects_k(auth_headers):
    lib_id, _, _ = _seed_vectors("cosine", auth_headers)
    # no build call
    r = client.post(
        f"/libraries/{lib_id}/chunks/search",
        json={"vector": [0.0, 1.0, 0.0], "k": 1, "metadata_filters": {}},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert len(r.json()["results"]) == 1


def test_search_with_metadata_filters(auth_headers):
    r = client.post("/libraries/", json={"name": "lib-meta2"}, headers=auth_headers)
    lib_id = r.json()["id"]
    r = client.post(f"/libraries/{lib_id}/documents", json={"title": "doc"}, headers=auth_headers)
    doc_id = r.json()["id"]
    client.post(
        f"/libraries/{lib_id}/chunks",
        json={
            "document_id": doc_id,
            "text": "x",
            "embedding": [0, 1, 0],
            "metadata": {"lang": "en", "topic": "a"},
        },
        headers=auth_headers,
    )
    client.post(
        f"/libraries/{lib_id}/chunks",
        json={
            "document_id": doc_id,
            "text": "y",
            "embedding": [1, 0, 0],
            "metadata": {"lang": "tr", "topic": "b"},
        },
        headers=auth_headers,
    )
    client.post(
        f"/libraries/{lib_id}/index", json={"algorithm": "linear", "metric": "cosine"}, headers=auth_headers
    )
    r = client.post(
        f"/libraries/{lib_id}/chunks/search",
        json={
            "vector": [0.0, 1.0, 0.0],
            "k": 5,
            "metadata_filters": {"lang": "en", "topic": "a"},
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    res = r.json()["results"]
    assert len(res) == 1
    assert res[0]["metadata"]["lang"] == "en"
    assert res[0]["metadata"]["topic"] == "a"
