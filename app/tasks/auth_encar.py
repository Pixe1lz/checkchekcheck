import asyncio
import traceback

from twocaptcha import TwoCaptcha
from playwright.async_api import async_playwright

from config import settings
from utils.logger import setup_logger
from services.utils import AsyncHTTPClient

logger = setup_logger(__name__)


async def check_request_encar():
    async with AsyncHTTPClient('https://example') as client:
        data = await client.get(
            endpoint='/endpoint',
            params={
                'param': 'example',
            }
        )
        return data


async def check_captcha_presence(page):
    try:
        recaptcha_v2 = await page.query_selector_all(
            ''
        )
        recaptcha_v3 = await page.evaluate(
            ''
        )

        return len(recaptcha_v2) > 0 or recaptcha_v3
    except Exception:
        logger.error(traceback.format_exc())
        logger.error('Ошибка при проверке наличия капчи')
        return False


async def solve_recaptcha_v2(page, url):
    sitekey = await page.evaluate(
        ''
    )

    if sitekey:
        logger.info(f'sitekey: {sitekey}')
        solver = TwoCaptcha(apiKey=settings.TWO_CAPTCHA_KEY)
        response = solver.recaptcha(sitekey=sitekey, url=url, invisible=0)
        code = response['code']
        logger.info(f'Код решенной капчи: {code}')
        await page.evaluate(
            ''
        )

        await page.wait_for_function(
            '',
            timeout=15_000
        )

        btn_selector = ''
        modal_selector = ''

        await page.click(btn_selector)
        try:
            async with page.expect_event('dialog', timeout=3000) if page.is_closed() else \
                    page.expect_selector(modal_selector, timeout=3000) as dialog_info:
                ...

            modal = await dialog_info.value
            if modal:
                logger.info('Обнаружено модальное окно')
                await page.click(f'{modal_selector} >> ')
                await asyncio.sleep(2)

        except Exception as e:
            logger.info('Модальное окно не появилось, продолжаем работу')
            await page.wait_for_timeout(1000)

        if await page.query_selector(btn_selector):
            logger.error('Кнопка всё ещё видна - капча не прошла')
            raise Exception('Не удалось подтвердить действие')
        else:
            logger.info('Успешный переход после капчи!')
    else:
        raise Exception('Не удалось извлечь sitekey')


async def auth():
    try:
        data = await check_request_encar()

        if data is not None:
            logger.info(f'Проверка API encar прошла успешно до авторизации (авторизация не требуется): {data}')
            return
    except Exception as e:
        logger.error(f'Ошибка запроса до авторизации: {str(e)}')

    async with async_playwright() as p:
        logger.info('Запуск браузера')

        try:
            browser = await p.chromium.launch(
                headless=True,
                channel='chrome',
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--start-maximized'
                ]
            )

            logger.info('Настройка браузера')
            context = await browser.new_context(
                locale='ru-RU',
                timezone_id='Europe/Moscow',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 YaBrowser/25.2.0.0 Safari/537.36',
                no_viewport=True
            )

            logger.info('Открытие сайта...')

            page = await context.new_page()

            await page.goto('http://example', wait_until='networkidle', timeout=50_000)

            await asyncio.sleep(10)
            await page.reload()
            await asyncio.sleep(60)

            has_captcha = await check_captcha_presence(page)

            if has_captcha:
                logger.info('Обнаружена капча, начинаем процесс решения')
                await solve_recaptcha_v2(page, page.url)
            else:
                logger.info('Капча не обнаружена, ожидаем 10 секунд')
                await asyncio.sleep(10)

            logger.info('Переход в каталог')
            await page.goto(
                'http://example/endpoint',
                timeout=30_000
            )
        except Exception:
            logger.error(traceback.format_exc())
            logger.info('Ошибка попытки авторизации на сайте encar')
        finally:
            await browser.close()
            logger.info('Закрытие браузера')

    logger.info('Проверка API encar после авторизации')
    data = await check_request_encar()
    if data is not None:
        logger.info(f'Проверка API encar после авторизации прошла успешно: {data}')
    else:
        logger.info('Проверка API encar после авторизации провалилась')


async def auth_encar_task():
    logger.info('Запуск задачи авторизации IP в encar')

    await auth()

    logger.info('Задача по авторизации encar выполнен')
