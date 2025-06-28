import json

from config import settings
from utils.logger import setup_logger
from services.utils import AsyncHTTPClient

logger = setup_logger(__name__)


async def KRW_updates_task():
    logger.info('Запуск задачи актуализации цен KRW и EUR')

    try:
        async with AsyncHTTPClient('https://example') as client:
            data = await client.get('/endpoint')
            data = json.loads(data)
            KRW = data['Valute']['KRW']
            EUR = data['Valute']['EUR']

            KRW_RATE = KRW['Value'] / KRW['Nominal']
            EUR_RATE = EUR['Value'] / EUR['Nominal']

            logger.info(
                f'\n'
                f'Цена KRW: {KRW_RATE}\n'
                f'Цена EUR: {EUR_RATE}'
            )

            settings.KRW_RATE = KRW['Value'] / KRW['Nominal']
            settings.EUR_RATE = EUR['Value'] / EUR['Nominal']

            logger.info('Задача по актуализации цен KRW и EUR выполнена успешно')
    except Exception as e:
        logger.error(f'Ошибка получения актуальной цены KRW и EUR: {str(e)}')
