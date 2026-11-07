"""Exclusão definitiva: proprietário, original e acessos compartilhados."""
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.models import Document, ShareLink
from tests.test_auth import ORIGIN, EMAIL_1, EMAIL_2, PASSWORD_1, PASSWORD_2
from tests.test_documents import auth_engine, auth_db, seeded_db, flow, make_pdf, upload, document  # noqa: F401


def switch(client, email, password):
    client.post('/auth/logout', headers={'Origin': ORIGIN})
    assert client.post('/auth/login', json={'email': email, 'password': password},
                       headers={'Origin': ORIGIN}).status_code == 200


def test_delete_removes_original_payload_and_redeemed_share(flow):
    client, ocr, converter, storage, db = flow
    info = document(client, upload(client, make_pdf(['Registro sintetico'])))
    path = '/documents/' + info['id']
    original = Path(db.get(Document, UUID(info['id'])).storage_path)
    invitation = client.post(path + '/shares', json={'email': EMAIL_2}, headers={'Origin': ORIGIN}).json()
    body = {'token': invitation['url'].split('share=')[1], 'password': invitation['password']}
    switch(client, EMAIL_2, PASSWORD_2)
    grant = client.post('/shares/redeem', json=body, headers={'Origin': ORIGIN}).json()['grant']
    switch(client, EMAIL_1, PASSWORD_1)
    response = client.delete(path, headers={'Origin': ORIGIN})
    assert response.status_code == 204 and response.content == b''
    assert not original.exists()
    db.expire_all()
    assert db.get(Document, UUID(info['id'])) is None
    assert db.scalar(select(ShareLink).where(ShareLink.document_id == UUID(info['id']))) is None
    assert client.get('/documents').json() == []
    for suffix in ('', '/original', '/json', '/pdf'):
        assert client.get(path + suffix).status_code == 404
    switch(client, EMAIL_2, PASSWORD_2)
    assert client.get('/shared/' + grant + '/json').status_code == 410
    assert client.post('/shares/redeem', json=body, headers={'Origin': ORIGIN}).status_code == 404


def test_delete_requires_owner_and_origin(flow):
    client, ocr, converter, storage, db = flow
    info = document(client, upload(client, make_pdf(['Registro sintetico'])))
    path = '/documents/' + info['id']
    for origin in (None, 'null', 'https://untrusted.example'):
        assert client.delete(path, headers={} if origin is None else {'Origin': origin}).status_code == 403
    client.post('/auth/logout', headers={'Origin': ORIGIN})
    assert client.delete(path, headers={'Origin': ORIGIN}).status_code == 401
    switch(client, EMAIL_2, PASSWORD_2)
    assert client.delete(path, headers={'Origin': ORIGIN}).status_code == 404
    assert len(list(storage.rglob('*.pdf'))) == 1


def test_delete_blocks_processing_and_rolls_back_on_file_error(flow, monkeypatch):
    client, ocr, converter, storage, db = flow
    info = document(client, upload(client, make_pdf(['Registro sintetico'])))
    ident = UUID(info['id'])
    row = db.get(Document, ident)
    path = '/documents/' + info['id']
    original = Path(row.storage_path)
    for status in ('queued', 'processing'):
        row.status = status
        db.commit()
        assert client.delete(path, headers={'Origin': ORIGIN}).status_code == 409
    row.status = 'error'
    db.commit()
    with monkeypatch.context() as patch:
        def denied(self, *args, **kwargs):
            raise PermissionError('Falha simulada')
        patch.setattr(Path, 'unlink', denied)
        assert client.delete(path, headers={'Origin': ORIGIN}).status_code == 503
    db.expire_all()
    assert db.get(Document, ident) is not None and original.exists()
    original.unlink()
    assert client.delete(path, headers={'Origin': ORIGIN}).status_code == 204
