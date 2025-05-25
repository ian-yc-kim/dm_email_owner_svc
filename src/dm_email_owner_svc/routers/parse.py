from fastapi import APIRouter
from typing import List
from dm_email_owner_svc.models.schema import ParseRequest, ParseResponse

parse_router = APIRouter()

@parse_router.post(
    "/parse",
    response_model=List[ParseResponse],
    status_code=200,
)
async def parse(req: ParseRequest) -> List[ParseResponse]:
    """
    Parse HTML content and map given emails to their owners.
    """
    # TODO: Implement business logic in service layer
    return []
