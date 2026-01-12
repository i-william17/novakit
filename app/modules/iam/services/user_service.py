import uuid
import hashlib
from typing import Optional, TYPE_CHECKING

from fastapi import Depends, HTTPException, Request
# from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.iam.hooks.security import hash_password, verify_password
from app.modules.iam.hooks.jwt_utils import decode_jwt
from app.common.db.sessions import get_db
from app.modules.iam.models.profile import Profile

from app.modules.iam.repositories.user_repository import UserRepository
from app.modules.iam.models.user import User
from app.modules.iam.hooks.user_status import UserStatus
from app.modules.iam.models.password_history import PasswordHistory
from app.modules.iam.schemas.user import UserCreate

if TYPE_CHECKING:
    from app.modules.iam.schemas.auth import ChangePasswordInput


repo = UserRepository()
# bearer_scheme = HTTPBearer()


# ---------------------------------------------------------
# Helper: set password
# ---------------------------------------------------------
async def set_password(db: AsyncSession, user: User, raw: str):
    user.password_hash = hash_password(raw)
    await db.flush()


class UserService:

    # -----------------------------------------------------
    # Basic Getters
    # -----------------------------------------------------
    async def find_by_id(self, db: AsyncSession, user_id: uuid.UUID):
        return await repo.get_by_id(db, user_id)

    async def find_by_username(self, db: AsyncSession, username: str):
        return await repo.get_by_username(db, username)

    async def find_by_jti(self, db: AsyncSession, jti: str):
        return await repo.get_by_jti(db, jti)

    async def register_user(self, db: AsyncSession, data: UserCreate) -> User:
        """
        Register a user with a required profile
        """
        # --------------------------------
        # 1. Business validations
        # --------------------------------
        if await repo.username_exists(db, data.username):
            raise ValueError("Username already taken")

        if await repo.email_exists(db, data.profile.email_address):
            raise ValueError("Email already registered")

        if await repo.phone_exists(db, data.profile.phone_number):
            raise ValueError("Phone number already registered")

        try:
            # --------------------------------
            # Create Profile
            # --------------------------------
            profile_id = uuid.uuid4().hex

            profile = Profile(
                id=profile_id,
                first_name=data.profile.first_name,
                middle_name=data.profile.middle_name,
                last_name=data.profile.last_name,
                email_address=data.profile.email_address,
                phone_number=data.profile.phone_number,
            )

            # --------------------------------
            # Create User
            # --------------------------------
            user = User(
                username=data.username,
                profile_id=profile_id,
                password_hash=hash_password(data.password),
                status=10,
            )

            db.add_all([profile, user])
            await db.commit()
            await db.refresh(user)

            return user

        except IntegrityError:
            await db.rollback()
            # DB-level safety net
            raise ValueError("User already exists")

        except Exception:
            await db.rollback()
            raise

    # -----------------------------------------------------
    # Password history helpers
    # -----------------------------------------------------
    @staticmethod
    async def check_password_history(db: AsyncSession, user: User, raw: str) -> bool:
        """Return True if password was used before."""
        digest = hashlib.md5(raw.encode()).hexdigest()
        return await repo.find_password_in_history(db, user, digest) is not None

    @staticmethod
    async def add_password_history(db: AsyncSession, user: User, raw: str):
        digest = hashlib.md5(raw.encode()).hexdigest()
        ph = PasswordHistory(user_id=user.user_id, old_password=digest)
        await repo.add_password_history(db, ph)

    # -----------------------------------------------------
    # Login credential validation
    # -----------------------------------------------------
    @staticmethod
    async def validate_credentials(db: AsyncSession, email_or_username: str, password: str):
        """
        Try login using email OR username.
        """

        # Step 1: find user
        # user = await repo.get_by_username(db, email_or_username)
        user = await repo.get_by_username_or_email(db, email_or_username)

        if not user:
            # If you later add get_by_email — also check email here
            # user = await repo.get_by_email(db, email_or_username)
            # if not user: ...
            return None, "Invalid email or password"

        # Step 2: compare password
        if not verify_password(password, user.password_hash):
            return None, "Invalid email or password"

        # Step 3: ensure status active
        if user.status != UserStatus.ACTIVE:
            return None, "User account is disabled"

        return user, None
    # -----------------------------------------------------
    # Full change-password validation
    # -----------------------------------------------------
    async def validate_change_password(
        self, db: AsyncSession, user: User, schema: "ChangePasswordInput"
    ):
        errors = {}

        # 1. Old password mismatch
        if not verify_password(schema.old_password, user.password_hash):
            errors["old_password"] = ["Incorrect password"]

        # 2. New password matches old password
        if schema.old_password == schema.new_password:
            errors["new_password"] = ["New password cannot be the same as old password"]

        # 3. Password reuse check
        reused = await self.check_password_history(db, user, schema.new_password)
        if reused:
            errors.setdefault("new_password", []).append(
                "Use a password you have never used before"
            )

        return errors if errors else None

    # -----------------------------------------------------
    # Lifecycle hook
    # -----------------------------------------------------
    async def after_save_purge_tokens(self, db: AsyncSession, user: User, changed_fields: list):
        if "password_hash" in changed_fields:
            await repo.purge_refresh_tokens(db, user.user_id)
            await db.commit()

    # -----------------------------------------------------
    # Create User
    # -----------------------------------------------------
    async def create_user(
        self, db: AsyncSession, username: str, password: str, profile_id: Optional[str] = None
    ) -> User:

        user = User(
            user_id=uuid.uuid4(),
            username=username,
            profile_id=profile_id,
            auth_key=uuid.uuid4().hex,
            password_hash=hash_password(password),
            status=10,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    # -----------------------------------------------------
    # Require Login (FastAPI dependency)
    # -----------------------------------------------------
    async def require_login(
            self,
            request: Request,
            db: AsyncSession = Depends(get_db),
    ) -> User:

        auth = getattr(request.state, "auth", None)

        if not auth:
            raise HTTPException(status_code=401, detail="Authentication required")

        payload = auth["payload"]
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = await repo.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User no longer exists")

        return user

    # -----------------------------------------------------
    # Change Password (final version)
    # -----------------------------------------------------
    async def change_password(
        self, db: AsyncSession, user: User, schema: "ChangePasswordInput"
    ):

        # Run validations
        errors = await self.validate_change_password(db, user, schema)
        if errors:
            raise HTTPException(
                status_code=422,
                detail={"errors": errors}
            )

        # 1. Update password
        user.password_hash = hash_password(schema.new_password)

        # 2. Add old password hash to history
        await self.add_password_history(db, user, schema.old_password)

        # 3. Purge refresh tokens
        await repo.purge_refresh_tokens(db, user.user_id)

        # 4. Save user
        await db.commit()
        await db.refresh(user)

        return True
