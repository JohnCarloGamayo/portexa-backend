import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.resume_library import ResumeLibraryItem, ResumeLibraryResponse
from app.services.resume_library import activate_resume, delete_resume, list_resumes, store_resume, save_customization, load_customization


router = APIRouter(prefix='/resumes', tags=['resumes'])


class CustomizationConfig(BaseModel):
    theme: str = 'light'
    accent: str = '#6366f1'
    bubbleStyle: str = 'rounded'
    showWelcomeMessage: bool = True


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


@router.patch('/{entry_id}/activate')
def activate_saved_resume(entry_id: str, current_user: User = Depends(get_current_user)):
    result = activate_resume(current_user.id, entry_id)
    if not result['activated']:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Resume not found')
    return result


@router.get('/customization', response_model=CustomizationConfig)
def get_customization(current_user: User = Depends(get_current_user)):
    return load_customization(current_user.id)


@router.put('/customization', response_model=CustomizationConfig)
def update_customization(
    config: CustomizationConfig,
    current_user: User = Depends(get_current_user)
):
    config_dict = config.model_dump()
    save_customization(current_user.id, config_dict)
    return config
