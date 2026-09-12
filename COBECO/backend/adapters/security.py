import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from backend.domain.errors import BusinessError


class TokenSecurity:
    def __init__(self, secret):
        self.secret = secret
        self.dummy_hash = self.hash("Dummy-password-123!")

    def hash(self, value):
        # Prehash also allows long Unicode security answers without bcrypt truncation.
        return bcrypt.hashpw(self.digest(value).encode(), bcrypt.gensalt(rounds=12)).decode()

    def verify(self, value, hashed):
        return bcrypt.checkpw(self.digest(value).encode(), hashed.encode())

    def digest(self, value):
        return hashlib.sha256(value.encode()).hexdigest()

    def tokens(self, user):
        now = datetime.now(UTC)
        base = {
            "sub": str(user["id"]),
            "version": user["session_version"],
            "iat": now,
            "iss": "cobeco",
            "aud": "cobeco",
        }
        access = jwt.encode({**base, "type": "access", "exp": now + timedelta(minutes=15)}, self.secret)
        refresh = jwt.encode(
            {**base, "type": "refresh", "jti": secrets.token_urlsafe(32), "exp": now + timedelta(days=7)},
            self.secret,
        )
        return {"access_token": access, "refresh_token": refresh}

    def decode(self, token, kind):
        try:
            data = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                audience="cobeco",
                issuer="cobeco",
                options={"require": ["exp", "iat", "sub", "version", "type"]},
            )
            if data["type"] != kind or not str(data["sub"]).isdigit():
                raise ValueError()
            return data
        except (jwt.InvalidTokenError, ValueError, TypeError):
            raise BusinessError("UNAUTHORIZED", "Sessão expirada. Entre novamente.", 401) from None
