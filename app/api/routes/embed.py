from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.openrouter import ask_openrouter
from app.services.resume_library import load_customization, get_active_resume


router = APIRouter(prefix='/embed', tags=['embed'])


class EmbedChatRequest(BaseModel):
    message: str
    portfolio_id: str


class EmbedChatResponse(BaseModel):
    response: str


@router.get('/customization/{portfolio_id}')
def get_embed_customization(portfolio_id: str):
    """
    Get customization for public embed chat.
    Portfolio ID is used to fetch user and their customization.
    """
    try:
        # Parse portfolio_id as user_id for now
        # In a real app, you'd have a mapping of portfolio_id to user_id
        user_id = int(portfolio_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid portfolio ID')

    customization = load_customization(user_id)
    return customization


@router.post('/rag-chat', response_model=EmbedChatResponse)
async def embed_rag_chat(request: EmbedChatRequest):
    """
    Public RAG-grounded chat endpoint for embedded widget.
    Uses portfolio_id to fetch user's active resume and customization.
    """
    try:
        user_id = int(request.portfolio_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid portfolio ID')

    # Get active resume for this user
    active_resume = get_active_resume(user_id)
    if not active_resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No resume found for this portfolio')

    resume_content = active_resume.get('raw_text', '')

    system_prompt = f"""You are an AI assistant representing a professional portfolio. Answer questions ONLY based on the following resume data. 
If the user asks something not covered in this data, politely refuse and stay on topic.

Resume Data:
{resume_content}

Guidelines:
- Be concise and professional
- Only answer about the person's experience, skills, and background
- Do not make up or infer information not in the resume
- Stay in character as the portfolio assistant"""
    
    try:
            result = await ask_openrouter(
                request.message,
                model='openrouter/auto',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': request.message},
                ],
            )
            return EmbedChatResponse(response=result['response'])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
