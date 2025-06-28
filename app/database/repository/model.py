from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from database.models import Model


class ModelRepository:
    def __init__(self, session: AsyncSession):
        self.model = Model
        self.session = session

    async def update_models(self, models: list[dict]):
        stmt = insert(Model).values(models)

        await self.session.execute(
            stmt.on_conflict_do_update(
                constraint='uq_code_brand_id',
                set_={
                    'action': stmt.excluded.action,
                    'display_value': stmt.excluded.display_value,
                    'eng_name': stmt.excluded.eng_name
                }
            ),
            execution_options={'echo': False}
        )
        await self.session.commit()

    async def get_all_models_actions(self) -> list[tuple]:
        result = await self.session.execute(select(Model.id, Model.action))
        return result.all()

    async def get_models(self, brand_id: int, page: int) -> list[tuple]:
        result = await self.session.execute(
            select(Model.id, Model.eng_name)
            .offset(page * 5)
            .limit(5)
            .where(Model.brand_id == brand_id)
            .order_by(Model.id)
        )
        return result.all()

    async def get_model_name(self, model_id: int) -> str:
        result = await self.session.execute(select(Model.eng_name).where(Model.id == model_id))
        return result.scalar()

    async def get_brand_id(self, model_id: int) -> int:
        result = await self.session.execute(
            select(Model.brand_id)
            .where(Model.id == model_id)
        )
        return result.scalar()
