from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from database.models import Configuration


class ConfigurationRepository:
    def __init__(self, session: AsyncSession):
        self.model = Configuration
        self.session = session

    async def update_configurations(self, configurations: list[dict]):
        stmt = insert(Configuration).values(configurations)

        await self.session.execute(
            stmt.on_conflict_do_update(
                constraint='uq_code_modification_id',
                set_={
                    'action': stmt.excluded.action,
                    'display_value': stmt.excluded.display_value,
                    'count': stmt.excluded.count
                }
            ),
            execution_options={'echo': False}
        )
        await self.session.commit()

    async def get_all_configuration_action(self, modification_id: int) -> list[tuple]:
        result = await self.session.execute(select(Configuration.action).where(Configuration.id == modification_id))
        return result.scalar()

    async def get_configurations(self, modification_id: int) -> list[tuple]:
        result = await self.session.execute(
            select(Configuration.id, Configuration.display_value, Configuration.count)
            .where(Configuration.modification_id == modification_id)
            .order_by(Configuration.id)
        )
        return result.all()

    async def get_configuration_name(self, configuration_id: int) -> str:
        result = await self.session.execute(select(Configuration.display_value).where(Configuration.id == configuration_id))
        return result.scalar()

    async def get_modification_id(self, configuration_id: int) -> int:
        result = await self.session.execute(
            select(Configuration.modification_id)
            .where(Configuration.id == configuration_id)
        )
        return result.scalar()

    async def get_action(self, configuration_id: int) -> str:
        result = await self.session.execute(
            select(Configuration.action)
            .where(Configuration.id == configuration_id)
        )
        return result.scalar()
