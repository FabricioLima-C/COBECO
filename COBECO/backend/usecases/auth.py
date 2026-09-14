import logging
import secrets
from datetime import UTC, datetime, timedelta

from backend.domain.errors import BusinessError
from backend.usecases.ports import Security, Store


def public_user(user):
    return {k: user[k] for k in ("id", "username", "name", "email", "created_at")}


def invalid():
    return BusinessError("INVALID_CREDENTIALS", "Credenciais inválidas.", 401)


class Auth:
    def __init__(self, store: Store, security: Security, limiter, settings):
        self.store, self.security, self.limiter, self.settings = store, security, limiter, settings

    def register(self, data):
        if data["username"].lower() == "demo":
            raise BusinessError("USERNAME_RESERVED", "Escolha outro username.")
        if self.settings.recovery_mode == "question" and (
            data["security_question"] == "Código de recuperação" or data["security_answer"] == "Não utilizado"
        ):
            raise BusinessError("SECURITY_ANSWER_REQUIRED", "Cadastre sua pergunta e resposta de segurança.")
        values = {
            "username": data["username"].lower(),
            "name": data["name"],
            "email": str(data["email"]).lower(),
            "password_hash": self.security.hash(data["password"]),
            "security_question": data["security_question"],
            "security_answer_hash": self.security.hash(
                data["security_answer"].strip().casefold()
                if self.settings.recovery_mode == "question"
                else secrets.token_urlsafe(32)
            ),
        }
        with self.store.transaction() as tx:
            user = tx.create_user(values)
            code = secrets.token_urlsafe(32)
            tx.set_recovery_code(user["id"], self.security.digest(code))
            return {**public_user(user), "recovery_code": code}

    def recovery_allowed(self, user):
        return user is not None and user["username"].lower() != "demo"

    def rotate_recovery_code(self, user_id, password):
        with self.store.transaction() as tx:
            user = tx.user(user_id=user_id)
            if not self.recovery_allowed(user) or not self.security.verify(password, user["password_hash"]):
                raise invalid()
            code = secrets.token_urlsafe(32)
            tx.set_recovery_code(user_id, self.security.digest(code))
            tx.update_user(user_id, reset_hash=None, reset_expires_at=None)
            return {"recovery_code": code}

    def login(self, username, password, ip):
        username = username.strip().lower()
        keys = [f"login:user:{username}", f"login:ip:{ip}"]
        with self.limiter.attempt(keys):
            with self.store.transaction() as tx:
                user = tx.user(username=username)
                hashed = user["password_hash"] if user else self.security.dummy_hash
                valid = self.security.verify(password, hashed)
                if not user or not valid or (username == "demo" and self.settings.app_env == "production"):
                    self.limiter.fail(keys)
                    raise invalid()
                self.limiter.clear(keys[0])
                user = tx.update_user(user["id"], session_version=user["session_version"] + 1)
                return self.issue(tx, user)

    def issue(self, tx, user):
        tokens = self.security.tokens(user)
        tx.update_user(user["id"], refresh_hash=self.security.digest(tokens["refresh_token"]))
        return {**tokens, "user": public_user(user)}

    def authenticate(self, token):
        payload = self.security.decode(token, "access")
        with self.store.transaction() as tx:
            user = tx.user(user_id=int(payload["sub"]))
            if (
                not user
                or user["session_version"] != payload["version"]
                or not user["refresh_hash"]
                or (user["username"] == "demo" and self.settings.app_env == "production")
            ):
                raise invalid()
            return public_user(user)

    def refresh(self, token):
        payload = self.security.decode(token, "refresh")
        with self.store.transaction() as tx:
            user = tx.user(user_id=int(payload["sub"]))
            if (
                not user
                or user["session_version"] != payload["version"]
                or not secrets.compare_digest(user["refresh_hash"] or "", self.security.digest(token))
                or (user["username"] == "demo" and self.settings.app_env == "production")
            ):
                raise invalid()
            return self.issue(tx, user)

    def logout(self, token):
        try:
            payload = self.security.decode(token, "refresh")
        except BusinessError:
            return
        with self.store.transaction() as tx:
            user = tx.user(user_id=int(payload["sub"]))
            if (
                user
                and user["session_version"] == payload["version"]
                and secrets.compare_digest(user["refresh_hash"] or "", self.security.digest(token))
            ):
                tx.update_user(user["id"], refresh_hash=None, session_version=user["session_version"] + 1)

    def recovery(self, username, ip):
        username = username.strip().lower()
        self.limiter.request(f"recovery-request:{ip}", 6, 900)
        if self.settings.recovery_mode != "log":
            return {
                "mode": self.settings.recovery_mode,
                "question": "Informe seu código de recuperação."
                if self.settings.recovery_mode == "code"
                else "Informe a resposta de segurança que você cadastrou.",
            }
        with self.store.transaction() as tx:
            user = tx.user(username=username)
            if self.recovery_allowed(user):
                token = secrets.token_urlsafe(32)
                tx.update_user(
                    user["id"],
                    reset_hash=self.security.digest(token),
                    reset_expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15),
                )
                logging.getLogger("cobeco.recovery").warning(
                    "Recuperação de desenvolvimento: %s/#reset?username=%s&token=%s",
                    self.settings.app_origin,
                    username,
                    token,
                )
        return {"mode": "log", "message": "Se a conta existir, o link estará no log de desenvolvimento."}

    def verify_recovery(self, username, answer, ip):
        if self.settings.recovery_mode == "log":
            raise BusinessError("RECOVERY_MODE", "Use o token do log de desenvolvimento.")
        username = username.strip().lower()
        keys = [f"reset:user:{username}", f"reset:ip:{ip}"]
        with self.limiter.attempt(keys, 3):
            with self.store.transaction() as tx:
                user = tx.user(username=username)
                if self.settings.recovery_mode == "code":
                    expected = tx.recovery_code(user["id"] if user else 0)
                    valid = secrets.compare_digest(self.security.digest(answer.strip()), expected or "0" * 64)
                else:
                    valid = self.security.verify(
                        answer.strip().casefold(),
                        user["security_answer_hash"] if user else self.security.dummy_hash,
                    )
                if not self.recovery_allowed(user) or not valid:
                    self.limiter.fail(keys, 3)
                    raise BusinessError("INVALID_RECOVERY", "Dados de recuperação inválidos.")
                token = secrets.token_urlsafe(32)
                tx.update_user(
                    user["id"],
                    reset_hash=self.security.digest(token),
                    reset_expires_at=datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=15),
                )
                self.limiter.clear(keys[0])
                return {"token": token}

    def reset(self, data, ip):
        username = data["username"].strip().lower()
        keys = [f"reset:user:{username}", f"reset:ip:{ip}"]
        with self.limiter.attempt(keys, 3):
            with self.store.transaction() as tx:
                user = tx.user(username=username)
                valid = False
                if user and user["reset_hash"] and user["reset_expires_at"] and data.get("token"):
                    valid = user["reset_expires_at"] > datetime.now(UTC).replace(
                        tzinfo=None
                    ) and secrets.compare_digest(
                        user["reset_hash"], self.security.digest(data.get("token") or "")
                    )
                if not self.recovery_allowed(user) or not valid:
                    self.limiter.fail(keys, 3)
                    raise BusinessError("INVALID_RECOVERY", "Dados de recuperação inválidos ou expirados.")
                tx.update_user(
                    user["id"],
                    password_hash=self.security.hash(data["new_password"]),
                    reset_hash=None,
                    reset_expires_at=None,
                    refresh_hash=None,
                    session_version=user["session_version"] + 1,
                )
                tx.set_recovery_code(user["id"], None)
                self.limiter.clear(keys[0])

    def update_profile(self, user_id, data):
        with self.store.transaction() as tx:
            user = tx.user(user_id=user_id)
            if not user or not self.security.verify(data["current_password"], user["password_hash"]):
                raise invalid()
            changes = {"name": data["name"], "email": str(data["email"]).lower()}
            if data.get("new_password"):
                if self.security.verify(data["new_password"], user["password_hash"]):
                    raise BusinessError("SAME_PASSWORD", "A nova senha deve ser diferente da atual.")
                changes.update(
                    password_hash=self.security.hash(data["new_password"]),
                    refresh_hash=None,
                    reset_hash=None,
                    reset_expires_at=None,
                    session_version=user["session_version"] + 1,
                )
                tx.set_recovery_code(user_id, None)
            return public_user(tx.update_user(user_id, **changes))
