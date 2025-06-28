from sqlalchemy import select, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from database.models import Brand


class BrandRepository:
    def __init__(self, session: AsyncSession):
        self.model = Brand
        self.session = session

    async def update_brands(self, brands: list[dict]) -> None:
        stmt = insert(Brand).values(brands)

        await self.session.execute(
            stmt.on_conflict_do_update(
                constraint='uq_brand_code',
                set_={
                    'action': stmt.excluded.action,
                    'display_value': stmt.excluded.display_value,
                    'eng_name': stmt.excluded.eng_name
                }
            ),
            execution_options={'echo': False}
        )
        await self.session.commit()

    async def get_all_brands_actions(self) -> list[tuple]:
        result = await self.session.execute(select(Brand.id, Brand.action))
        return result.all()

    async def get_brands(self, page: int) -> list[tuple]:
        priority_brands = [
            'BMW',
            'Mercedes-Benz',
            'Audi',
            'Porsche',
            'Rolls-Royce',
            'Bentley',
            'Kia',
            'Hyundai',
            'Chevrolet',
            'Ford',
            'Genesis'
        ]

        priority_order = case(
            {brand: idx for idx, brand in enumerate(priority_brands)},
            value=Brand.eng_name,
            else_=len(priority_brands)
        )

        result = await self.session.execute(
            select(Brand.id, Brand.eng_name)
            .offset(page * 5)
            .limit(5)
            .order_by(priority_order, Brand.eng_name)
        )
        return result.all()

    async def get_brand_name(self, brand_id: int) -> str:
        result = await self.session.execute(select(Brand.eng_name).where(Brand.id == brand_id))
        return result.scalar()
