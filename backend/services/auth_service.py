from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from config import settings

bearer = HTTPBearer(auto_error=False)

_supabase: Client | None = None


def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        _supabase = create_client(settings.supabase_url, settings.supabase_secret_key)
    return _supabase


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        sb = get_supabase()
        response = sb.auth.get_user(credentials.credentials)
        if not response or not response.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"id": response.user.id, "email": response.user.email}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict | None:
    if not credentials:
        return None
    try:
        sb = get_supabase()
        response = sb.auth.get_user(credentials.credentials)
        if response and response.user:
            return {"id": response.user.id, "email": response.user.email}
    except Exception:
        pass
    return None
