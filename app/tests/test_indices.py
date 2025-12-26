from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _setup_lib_with_vectors(metric: str, auth_headers):
    r = client.post("/libraries/", json={"name": f"lib-{metric}"}, headers=auth_headers)
    lib_id = r.json()["id"]
    r = client.post(f"/libraries/{lib_id}/documents", json={"title": "doc"}, headers=auth_headers)
    doc_id = r.json()["id"]
    # two orthogonal-ish vectors
    v1 = [0.0, 1.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    client.post(
        f"/libraries/{lib_id}/chunks",
        json={"document_id": doc_id, "text": "a", "embedding": v1},
        headers=auth_headers,
    )
    client.post(
        f"/libraries/{lib_id}/chunks",
        json={"document_id": doc_id, "text": "b", "embedding": v2},
        headers=auth_headers,
    )
    return lib_id


def test_kdtree_euclidean(auth_headers):
    lib_id = _setup_lib_with_vectors("euclidean", auth_headers)
    r = client.put(
        f"/libraries/{lib_id}/index",
        json={"algorithm": "kdtree", "metric": "euclidean"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    r = client.post(
        f"/libraries/{lib_id}/chunks/search",
        json={"vector": [0.0, 1.0, 0.0], "k": 1, "metadata_filters": {}},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert len(r.json()["results"]) == 1


def test_lsh_cosine(auth_headers):
    lib_id = _setup_lib_with_vectors("cosine", auth_headers)
    r = client.put(
        f"/libraries/{lib_id}/index", json={"algorithm": "lsh", "metric": "cosine"}, headers=auth_headers
    )
    assert r.status_code == 200
    r = client.post(
        f"/libraries/{lib_id}/chunks/search",
        json={"vector": [1.0, 0.0, 0.0], "k": 1, "metadata_filters": {}},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert len(r.json()["results"]) == 1


def test_metadata_filtering(auth_headers):
    r = client.post("/libraries/", json={"name": "lib-meta"}, headers=auth_headers)
    lib_id = r.json()["id"]
    r = client.post(f"/libraries/{lib_id}/documents", json={"title": "doc"}, headers=auth_headers)
    doc_id = r.json()["id"]
    client.post(
        f"/libraries/{lib_id}/chunks",
        json={
            "document_id": doc_id,
            "text": "x",
            "embedding": [0, 1, 0],
            "metadata": {"lang": "en"},
        },
        headers=auth_headers,
    )
    client.post(
        f"/libraries/{lib_id}/chunks",
        json={
            "document_id": doc_id,
            "text": "y",
            "embedding": [1, 0, 0],
            "metadata": {"lang": "tr"},
        },
        headers=auth_headers,
    )
    client.put(
        f"/libraries/{lib_id}/index", json={"algorithm": "linear", "metric": "cosine"}, headers=auth_headers
    )
    r = client.post(
        f"/libraries/{lib_id}/chunks/search",
        json={
            "vector": [0.0, 1.0, 0.0],
            "k": 5,
            "metadata_filters": {"lang": "en"},
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) == 1
    assert results[0]["metadata"]["lang"] == "en"
