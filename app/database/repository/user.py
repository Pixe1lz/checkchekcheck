from datetime import datetime, timedelta, UTC

from sqlalchemy import select, update, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from aiogram import types

from database.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.model = User
        self.session = session

    async def is_exist(self, user_id) -> bool:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none() is not None

    async def create_user(self, user: types.User) -> None:
        await self.session.execute(
            insert(User)
            .values(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name
            )
        )
        await self.session.commit()

    async def update_user(self, user: types.User) -> None:
        await self.session.execute(
            update(User)
            .values(
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name
            )
            .where(User.id == user.id)
        )
        await self.session.commit()

    async def get_user(self, user_id) -> User:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar()

    async def is_blocked(self, user_id) -> bool:
        result = await self.session.execute(select(User.is_blocked).where(User.id == user_id))
        return result.scalar()

    async def ban(self, user_id) -> None:
        await self.session.execute(update(User).values(is_blocked=True).where(User.id == user_id))
        await self.session.commit()

    async def unban(self, user_id) -> None:
        await self.session.execute(update(User).values(is_blocked=False).where(User.id == user_id))
        await self.session.commit()

    async def get_statistics(self) -> dict:
        current_time = datetime.now(UTC)

        today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)


        result = await self.session.execute(
            select(
                func.count(
                    case((User.started_at >= today, 1))
                ).label('today'),

                func.count(
                    case((
                        and_(
                            User.started_at >= today - timedelta(days=1),
                            User.started_at < today
                        ), 1))
                ).label('yesterday'),

                func.count(
                    case((User.started_at >= today - timedelta(days=3), 1))
                ).label('last_3_days'),

                func.count(
                    case((User.started_at >= today - timedelta(days=7), 1))
                ).label('last_7_days')
            )
        )

        stats = result.first()

        return {
            'today': stats.today,
            'yesterday': stats.yesterday,
            'last_3_days': stats.last_3_days,
            'last_7_days': stats.last_7_days
        }

    async def get_all_users(self, only_id: bool = False) -> list[User] | list[int]:
        if only_id:
            result = await self.session.execute(select(User.id))
        else:
            result = await self.session.execute(select(User).order_by(User.started_at.desc()))

        return result.scalars().all()