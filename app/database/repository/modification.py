from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from database.models import Modification


class ModificationRepository:
    def __init__(self, session: AsyncSession):
        self.model = Modification
        self.session = session

    async def update_modifications(self, modifications: list[dict]):
        stmt = insert(Modification).values(modifications)

        await self.session.execute(
            stmt.on_conflict_do_update(
                constraint='uq_code_generation_id',
                set_={
                    'action': stmt.excluded.action,
                    'display_value': stmt.excluded.display_value
                }
            ),
            execution_options={'echo': False}
        )
        await self.session.commit()

    async def get_all_modification_actions(self) -> list[tuple]:
        result = await self.session.execute(select(Modification.id, Modification.action))
        return result.all()

    async def get_modifications(self, generation_id: int) -> list[tuple]:
        result = await self.session.execute(
            select(Modification.id, Modification.display_value)
            .where(Modification.generation_id == generation_id)
            .order_by(Modification.id)
        )
        return result.all()

    async def get_modification_name(self, modification_id: int) -> str:
        result = await self.session.execute(select(Modification.display_value).where(Modification.id == modification_id))
        return result.scalar()

    async def get_generation_id(self, modification_id: int) -> int:
        result = await self.session.execute(
            select(Modification.generation_id)
            .where(Modification.id == modification_id)
        )
        return result.scalar()
