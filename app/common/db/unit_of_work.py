from typing import Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.db.transaction import transaction

class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def run(self, func: Callable[..., Awaitable], *args, **kwargs):
        async with transaction(self.session):
            return await func(*args, **kwargs)






# from app.database.unit_of_work import UnitOfWork
#
# class UserService:
#
#     @staticmethod
#     async def create_user_with_history(db: AsyncSession, username: str, password: str):
#         uow = UnitOfWork(db)
#
#         async def logic():
#             user = User(
#                 user_id=uuid.uuid4(),
#                 username=username,
#                 password_hash=UserService.hash_password(password),
#                 status=10,
#             )
#             db.add(user)
#
#             history = PasswordHistory(
#                 user_id=user.user_id,
#                 old_password=md5(password.encode()).hexdigest(),
#             )
#             db.add(history)
#
#             return user
#
#         return await uow.run(logic)


# @router.post("/register")
# async def register(data: RegisterSchema, db=Depends(get_db)):
#     return await UserService.create_user_with_history(db, data.username, data.password)
