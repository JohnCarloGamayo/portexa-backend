import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.resume_library import ResumeLibraryItem, ResumeLibraryResponse
from app.services.resume_library import delete_resume, list_resumes, store_resume


router = APIRouter(prefix='/resumes', tags=['resumes'])


@router.get('', response_model=ResumeLibraryResponse)
def get_resumes(current_user: User = Depends(get_current_user)):
    return list_resumes(current_user.id)


@router.post('', response_model=ResumeLibraryItem)
async def add_resume(
    file: UploadFile = File(...),
    index_json: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    try:
        index = json.loads(index_json)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid resume index payload') from error

    return await store_resume(current_user.id, file, index)


@router.delete('/{entry_id}')
def remove_resume(entry_id: str, current_user: User = Depends(get_current_user)):
    result = delete_resume(current_user.id, entry_id)
    if not result['deleted']:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Resume not found')
    return result
