from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt


class JWTHandler:
    def __init__(self, secret_key: str, algorithm: str, access_token_expire_minutes: str):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_seconds = 24 * 60 * 60

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(
                seconds=self.access_token_expire_seconds)
        )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, self.secret_key, algorithm=self.algorithm)
        # print("exp",expire)
        return encoded_jwt

    def decode_jwt(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret_key,
                                 algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.JWTError as e:
            raise Exception(f"Token is invalid: {str(e)}")
