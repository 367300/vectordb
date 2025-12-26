from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_persistence_save_load_and_search_restored(tmp_path: Path, auth_headers) -> None:
    r = client.post("/libraries/", json={"name": "lib-persist"}, headers=auth_headers)
    assert r.status_code == 201
    lib_id = r.json()["id"]

    r = client.post(f"/libraries/{lib_id}/documents", json={"title": "doc"}, headers=auth_headers)
    assert r.status_code == 201
    doc_id = r.json()["id"]

    v1 = [0.0, 1.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    r = client.post(
        f"/libraries/{lib_id}/chunks",
        json={"document_id": doc_id, "text": "a", "embedding": v1},
        headers=auth_headers,
    )
    assert r.status_code == 201
    r = client.post(
        f"/libraries/{lib_id}/chunks",
        json={"document_id": doc_id, "text": "b", "embedding": v2},
        headers=auth_headers,
    )
    assert r.status_code == 201

    r = client.put(
        f"/libraries/{lib_id}/index",
        json={"algorithm": "kdtree", "metric": "euclidean"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    info = r.json()
    assert info["algorithm"] == "kdtree"
    assert info["metric"] == "euclidean"

    r = client.post(
        f"/libraries/{lib_id}/chunks/search",
        json={"vector": v1, "k": 1, "metadata_filters": {}},
        headers=auth_headers,
    )
    assert r.status_code == 200
    before = r.json()["results"][0]["chunk_id"]

    snap_path = tmp_path / "snapshot.json"

    r = client.post("/admin/snapshots", headers=auth_headers)
    assert r.status_code == 201  # RESTful: POST creates resource, returns 201
    snapshot_data = r.json()
    snapshot_id = snapshot_data["id"]
    saved_path = Path(snapshot_data["path"]).resolve()
    snap_path.write_text(saved_path.read_text())

    # Use the new RESTful restore endpoint
    r = client.post(f"/admin/snapshots/{snapshot_id}/restore", headers=auth_headers)
    assert r.status_code == 200  # OK for synchronous operation

    r = client.post(
        f"/libraries/{lib_id}/chunks/search",
        json={"vector": v1, "k": 1, "metadata_filters": {}},
        headers=auth_headers,
    )
    assert r.status_code == 200
    after = r.json()["results"][0]["chunk_id"]
    assert before == after

    r = client.put(
        f"/libraries/{lib_id}/index",
        json={"algorithm": "kdtree", "metric": "euclidean"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    info2 = r.json()
    assert info2["algorithm"] == "kdtree"
    assert info2["metric"] == "euclidean"
