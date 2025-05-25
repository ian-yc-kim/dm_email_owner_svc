from fastapi import APIRouter, Depends, HTTPException, status
import json
import logging
from typing import List

from dm_email_owner_svc.models.schema import ParseRequest, ParseResponse
from dm_email_owner_svc.dependencies.openai_dependency import get_openai_client
from dm_email_owner_svc.core.prompts import build_email_owner_prompt


parse_router = APIRouter()

@parse_router.post(
    "/parse",
    response_model=List[ParseResponse],
    status_code=200,
)
async def parse_emails(req: ParseRequest, openai_client=Depends(get_openai_client)) -> List[ParseResponse]:
    """
    Parse HTML content and map given emails to their owners.
    """
    messages = build_email_owner_prompt(req.html_content, req.emails)
    result = openai_client.chat_completion(messages)
    if result.get('error'):
        raise HTTPException(status_code=502, detail="Downstream API error")
    try:
        content = result['choices'][0]['message']['content']
        parsed = json.loads(content)
    except Exception as e:
        logging.error(e, exc_info=True)
        raise HTTPException(status_code=502, detail="Error parsing response from AI")
    output = []
    for email in req.emails:
        owner = "unknown"
        for entry in parsed:
            if entry.get("email") == email:
                owner = entry.get("owner", "unknown")
                break
        output.append(ParseResponse(email=email, owner=owner))
    return output
