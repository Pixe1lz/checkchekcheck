from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from database.models import CarViewingHistory


class CarViewingHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.model = CarViewingHistory
        self.session = session

    async def save(self, user_id: int, car_id: int) -> None:
        await self.session.execute(
            insert(CarViewingHistory).
            values(
                user_id=user_id,
                car_id=car_id,
            )
        )
        await self.session.commit()

    async def is_viewed(self, user_id: int, car_id: int) -> bool:
        result = await self.session.execute(
            select(CarViewingHistory)
            .where(
                CarViewingHistory.user_id == user_id,
                CarViewingHistory.car_id == car_id
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
