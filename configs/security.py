from fastapi import status, HTTPException, Depends
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import typing

from configs.config import SettingsManager

class UnauthorizedMessage(BaseModel):
    detail: str = "Bearer token missing or unknown"


async def get_token(
    auth: typing.Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> str:
    token = auth.credentials if auth else None
    authenticate_not_match = auth is None or token != SettingsManager.settings.api_token
    if authenticate_not_match:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=UnauthorizedMessage().detail,
        )
    return token