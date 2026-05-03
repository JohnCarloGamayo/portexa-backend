from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


BASE_DIR = Path(__file__).resolve().parents[2] / 'storage' / 'resumes'


def _user_dir(user_id: int) -> Path:
    return BASE_DIR / str(user_id)


def _manifest_path(user_id: int) -> Path:
    return _user_dir(user_id) / 'manifest.json'


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r'[^A-Za-z0-9._-]+', '_', filename).strip('._')
    return cleaned or 'resume.bin'


def _default_manifest() -> dict:
    return {'active_id': None, 'items': []}


def load_manifest(user_id: int) -> dict:
    manifest_file = _manifest_path(user_id)
    if not manifest_file.exists():
        return _default_manifest()

    try:
        data = json.loads(manifest_file.read_text(encoding='utf-8'))
        if isinstance(data, dict):
            data.setdefault('active_id', None)
            data.setdefault('items', [])
            return data
    except Exception:
        pass

    return _default_manifest()


def save_manifest(user_id: int, manifest: dict) -> None:
    user_dir = _user_dir(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    _manifest_path(user_id).write_text(json.dumps(manifest, indent=2), encoding='utf-8')


def list_resumes(user_id: int) -> dict:
    manifest = load_manifest(user_id)
    items = sorted(manifest.get('items', []), key=lambda item: item.get('indexed_at', ''), reverse=True)
    active_id = manifest.get('active_id')

    for item in items:
        item['is_active'] = item.get('id') == active_id

    return {'active_id': active_id, 'items': items}


async def store_resume(user_id: int, upload: UploadFile, index: dict) -> dict:
    user_dir = _user_dir(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    entry_id = uuid4().hex
    safe_name = _safe_filename(upload.filename or 'resume.bin')
    stored_name = f'{entry_id}_{safe_name}'
    stored_path = user_dir / stored_name

    contents = await upload.read()
    stored_path.write_bytes(contents)

    manifest = load_manifest(user_id)
    item = {
        'id': entry_id,
        'file_name': index.get('fileName') or index.get('file_name') or upload.filename or 'Resume',
        'source_type': index.get('sourceType') or index.get('source_type') or upload.content_type or 'unknown',
        'indexed_at': index.get('indexedAt') or index.get('indexed_at'),
        'name': index.get('name') or 'Untitled Candidate',
        'summary': index.get('summary') or 'Resume indexed successfully.',
        'experience': index.get('experience') or [],
        'education': index.get('education') or [],
        'skills': index.get('skills') or [],
        'raw_text': index.get('rawText') or index.get('raw_text') or '',
        'size_bytes': len(contents),
        'stored_file_name': stored_name,
        'is_active': True,
    }

    manifest['items'] = [existing for existing in manifest.get('items', []) if existing.get('id') != entry_id]
    manifest['items'].insert(0, item)
    manifest['active_id'] = entry_id
    save_manifest(user_id, manifest)

    return item


def delete_resume(user_id: int, entry_id: str) -> dict:
    manifest = load_manifest(user_id)
    remaining = []
    deleted_item = None

    for item in manifest.get('items', []):
        if item.get('id') == entry_id:
            deleted_item = item
            stored_name = item.get('stored_file_name')
            if stored_name:
                stored_path = _user_dir(user_id) / stored_name
                if stored_path.exists():
                    stored_path.unlink()
            continue
        remaining.append(item)

    manifest['items'] = remaining
    if manifest.get('active_id') == entry_id:
        manifest['active_id'] = remaining[0]['id'] if remaining else None

    save_manifest(user_id, manifest)
    return {'deleted': deleted_item is not None, 'active_id': manifest.get('active_id')}


def activate_resume(user_id: int, entry_id: str) -> dict:
    manifest = load_manifest(user_id)
    items = manifest.get('items', [])
    target = next((item for item in items if item.get('id') == entry_id), None)

    if target is None:
        return {'activated': False, 'active_id': manifest.get('active_id')}

    manifest['active_id'] = entry_id
    save_manifest(user_id, manifest)
    return {'activated': True, 'active_id': entry_id}


def get_active_resume(user_id: int) -> dict | None:
    manifest = load_manifest(user_id)
    items = manifest.get('items', [])
    if not items:
        return None

    active_id = manifest.get('active_id')
    if active_id:
        active_item = next((item for item in items if item.get('id') == active_id), None)
        if active_item is not None:
            return active_item

    return items[0]


def _customization_path(user_id: int) -> Path:
    return _user_dir(user_id) / 'customization.json'


def save_customization(user_id: int, customization: dict) -> None:
    user_dir = _user_dir(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    _customization_path(user_id).write_text(json.dumps(customization, indent=2), encoding='utf-8')


def load_customization(user_id: int) -> dict:
    customization_file = _customization_path(user_id)
    if not customization_file.exists():
        return {'theme': 'light', 'accent': '#6366f1', 'bubbleStyle': 'rounded', 'showWelcomeMessage': True}

    try:
        data = json.loads(customization_file.read_text(encoding='utf-8'))
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {'theme': 'light', 'accent': '#6366f1', 'bubbleStyle': 'rounded', 'showWelcomeMessage': True}
