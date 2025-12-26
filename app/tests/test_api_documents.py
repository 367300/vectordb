from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_library(auth_headers) -> str:
    r = client.post("/libraries/", json={"name": "lib-docs"}, headers=auth_headers)
    return r.json()["id"]


def _create_document(library_id: str, auth_headers) -> str:
    r = client.post(f"/libraries/{library_id}/documents", json={"title": "doc"}, headers=auth_headers)
    assert r.status_code == 201
    return r.json()["id"]


def test_documents_crud_flow(auth_headers):
    lib_id = _create_library(auth_headers)

    # create
    doc_id = _create_document(lib_id, auth_headers)

    # list
    r = client.get(f"/libraries/{lib_id}/documents", headers=auth_headers)
    assert r.status_code == 200
    assert any(x["id"] == doc_id for x in r.json())

    # update
    r = client.patch(
        f"/libraries/{lib_id}/documents/{doc_id}",
        json={"title": "doc-upd", "description": "dx", "metadata": {"x": "y"}},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "doc-upd"
    assert data["description"] == "dx"
    assert data["metadata"]["x"] == "y"

    # delete
    r = client.delete(f"/libraries/{lib_id}/documents/{doc_id}", headers=auth_headers)
    assert r.status_code == 204

    # update after delete -> 404
    r = client.patch(f"/libraries/{lib_id}/documents/{doc_id}", json={"title": "z"}, headers=auth_headers)
    assert r.status_code == 404


def test_create_document_not_found_library(auth_headers):
    r = client.post("/libraries/bad-lib/documents", json={"title": "doc"}, headers=auth_headers)
    assert r.status_code == 404
