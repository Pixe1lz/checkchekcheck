from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from database.models import Generation


class GenerationRepository:
    def __init__(self, session: AsyncSession):
        self.model = Generation
        self.session = session

    async def update_generations(self, generations: list[dict]):
        stmt = insert(Generation).values(generations)

        await self.session.execute(
            stmt.on_conflict_do_update(
                constraint='uq_code_model_id',
                set_={
                    'action': stmt.excluded.action,
                    'display_value': stmt.excluded.display_value,
                    'start_year': stmt.excluded.start_year,
                    'end_year': stmt.excluded.end_year
                }
            ),
            execution_options={'echo': False}
        )
        await self.session.commit()

    async def get_all_generation_actions(self) -> list[tuple]:
        result = await self.session.execute(select(Generation.id, Generation.action))
        return result.all()

    async def get_generations(self, model_id: int) -> list[tuple]:
        result = await self.session.execute(
            select(Generation.id, Generation.display_value, Generation.start_year, Generation.end_year)
            .where(Generation.model_id == model_id)
            .order_by(Generation.id)
        )
        return result.all()

    async def get_generation_name(self, generation_id: int) -> str:
        result = await self.session.execute(select(Generation.display_value).where(Generation.id == generation_id))
        return result.scalar()

    async def get_model_id(self, model_id: int) -> int:
        result = await self.session.execute(
            select(Generation.model_id)
            .where(Generation.id == model_id)
        )
        return result.scalar()
