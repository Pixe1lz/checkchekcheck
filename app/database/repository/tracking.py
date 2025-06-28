from sqlalchemy import func, select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Tracking


class TrackingRepository:
    def __init__(self, session: AsyncSession):
        self.model = Tracking
        self.session = session

    async def tracking_create(self, user_id: int, configuration_id: int, release_year: str | None, mileage: str | None, price: str | None) -> Tracking:
        track = Tracking(
            user_id=user_id,
            configuration_id=configuration_id,
            release_year=release_year,
            mileage=mileage,
            price=price,
            car_ids=[]
        )
        self.session.add(track)
        await self.session.commit()
        await self.session.refresh(track)
        return track

    async def tracking_count(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Tracking.id))
            .where(Tracking.user_id == user_id)
        )
        return result.scalar()

    async def tracking_list(self, user_id: int, page: int) -> list[Tracking]:
        result = await self.session.execute(
            select(Tracking)
            .where(Tracking.user_id == user_id)
            .offset(page * 10)
            .limit(10)
            .order_by(Tracking.id)
        )
        return result.scalars().all()

    async def track_get(self, track_id: int) -> Tracking:
        result = await self.session.execute(
            select(Tracking)
            .where(Tracking.id == track_id)
        )
        return result.scalar()

    async def tracking_delete(self, track_id: int) -> None:
        await self.session.execute(
            delete(Tracking)
            .where(
                Tracking.id == track_id
            )
        )
        await self.session.commit()

    async def update_car_ids(self, track_id: int, car_ids: list[int]) -> None:
        await self.session.execute(
            update(Tracking)
            .values(car_ids=car_ids)
            .where(Tracking.id == track_id)
        )
        await self.session.commit()

    async def tracking_list_all(self) -> list[Tracking]:
        result = await self.session.execute(select(Tracking))
        return result.scalars().all()

    async def activate_track(self, track_id: int) -> None:
        await self.session.execute(
            update(Tracking)
            .values(is_active=True)
            .where(Tracking.id == track_id)
        )
