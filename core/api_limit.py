from src.backend.core.limiter import AsyncRateLimiter
from src.backend.utils.api_utils import redis_manager
from src.backend.db import mongodb
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
# apiSecurity = Annotated[str, Depends(oauth2_scheme)]

AsyncRateLimiter.set_enable(True)
class GetCurrentUser:
    def __init__(self, limit_key: str):
        self.limiter = AsyncRateLimiter(redis_manager)
        self.limit_key = limit_key

    async def __call__(self, token: Annotated[str, Depends(oauth2_scheme)], req: Request):
        route = req.scope.get("route")
        route_path = route.path if route else "unknown"

        user = await mongodb.get_user_by_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        await self.limiter.check_rate_limit(str(user.id), route_path, self.limit_key)

        return user

apiSecurityStrict = Annotated[mongodb.Users, Depends(GetCurrentUser("strict"))]
apiSecurityStandard = Annotated[mongodb.Users, Depends(GetCurrentUser("standard"))]
apiSecurityRelaxed = Annotated[mongodb.Users, Depends(GetCurrentUser("relaxed"))]
apiSecurityFree = Annotated[mongodb.Users, Depends(GetCurrentUser("free"))]