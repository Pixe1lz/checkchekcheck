from typing import List, Dict, Any

from utils.logger import setup_logger
from database.base import get_db
from services.utils import AsyncHTTPClient
from database.repository.brand import BrandRepository
from database.repository.model import ModelRepository
from database.repository.generation import GenerationRepository
from database.repository.modification import ModificationRepository
from database.repository.configuration import ConfigurationRepository

logger = setup_logger(__name__)


async def insert_brands():
    async with AsyncHTTPClient('https://example.com') as client:
        brands_data = await client.get(
            endpoint='/endpoint',
            params={
                'params': 'example',
            }
        )

    brands = []
    for node in brands_data['iNav']['Nodes']:
        if node['Name'] == 'CarType':
            for facet in node['Facets']:
                if facet['IsSelected'] is True:
                    for brand in facet['Refinements']['Nodes'][0]['Facets']:
                        brands.append(
                            {
                                'code': brand['Metadata']['Code'][0],
                                'action': brand['Action'],
                                'display_value': brand['DisplayValue'],
                                'eng_name': brand['Metadata']['EngName'][0]
                            }
                        )
                    break
            break

    async with get_db() as session:
        brand_repo = BrandRepository(session)
        await brand_repo.update_brands(brands)


async def insert_models():
    async with get_db() as session:
        brand_repo = BrandRepository(session)
        brands: list[tuple] = await brand_repo.get_all_brands_actions()

    models = []
    for brand_id, action in brands:
        try:
            async with AsyncHTTPClient('https://example') as client:
                models_data = await client.get(
                    endpoint='/endpoint',
                    params={
                        'param': 'example',
                    }
                )
        except Exception as e:
            logger.error(f'Ошибка получение моделей бренда ({bran_id}): {str(e)}')
            continue

        for node in models_data['iNav']['Nodes']:
            if node['Name'] == 'CarType':
                for facet in node['Facets']:
                    if facet['IsSelected'] is True:
                        for i in facet['Refinements']['Nodes'][0]['Facets']:
                            if i['IsSelected'] is True:
                                for model in i['Refinements']['Nodes'][0]['Facets']:
                                    models.append(
                                        {
                                            'code': model['Metadata']['Code'][0],
                                            'action': model['Action'],
                                            'display_value': model['DisplayValue'],
                                            'eng_name': model['Metadata']['EngName'][0],
                                            'brand_id': brand_id
                                        }
                                    )

                                break
                        break
                break

    async with get_db() as session:
        model_repo = ModelRepository(session)
        await model_repo.update_models(models)


async def insert_generations():
    async with get_db() as session:
        model_repo = ModelRepository(session)
        models: list[tuple] = await model_repo.get_all_models_actions()

    generations = []
    for model_id, action in models:
        try:
            async with AsyncHTTPClient('https://examle') as client:
                generations_data = await client.get(
                    endpoint='/endpoint',
                    params={
                        'param': 'example',
                    }
                )
        except Exception as e:
            logger.error(f'Ошибка получение поколений модели ({model_id}): {str(e)}')
            continue

        for node in generations_data['iNav']['Nodes']:
            if node['Name'] == 'CarType':
                for facet in node['Facets']:
                    if facet['IsSelected'] is True:
                        for i in facet['Refinements']['Nodes'][0]['Facets']:
                            if i['IsSelected'] is True:
                                for model in i['Refinements']['Nodes'][0]['Facets']:
                                    if model['IsSelected'] is True:
                                        for generation in model['Refinements']['Nodes'][0]['Facets']:
                                            start_year = None
                                            end_year = None

                                            if generation['Metadata']['ModelStartDate']:
                                                if generation['Metadata']['ModelStartDate'] != [None]:
                                                    start_year = int(generation['Metadata']['ModelStartDate'][0][:4])

                                            if generation['Metadata']['ModelEndDate']:
                                                if generation['Metadata']['ModelEndDate'] != [None]:
                                                    end_year = int(generation['Metadata']['ModelEndDate'][0][:4])

                                            generations.append(
                                                {
                                                    'code': generation['Metadata']['Code'][0],
                                                    'action': generation['Action'],
                                                    'display_value': generation['DisplayValue'],
                                                    'model_id': model_id,
                                                    'start_year': start_year,
                                                    'end_year': end_year
                                                }
                                            )

                                        break
                                break
                        break
                break

    async with get_db() as session:
        generation_repo = GenerationRepository(session)
        await generation_repo.update_generations(generations)


async def insert_modifications():
    async with get_db() as session:
        generation_repo = GenerationRepository(session)
        generations: list[tuple] = await generation_repo.get_all_generation_actions()

    modifications = []
    for generation_id, action in generations:
        try:
            async with AsyncHTTPClient('https://example') as client:
                modifications_data = await client.get(
                    endpoint='/endpoint',
                    params={
                        'param': 'example',
                    }
                )
        except Exception as e:
            logger.error(f'Ошибка получение модификации поколения ({generation_id}): {str(e)}')
            continue

        for node in modifications_data['iNav']['Nodes']:
            if node['Name'] == 'CarType':
                for facet in node['Facets']:
                    if facet['IsSelected'] is True:
                        for i in facet['Refinements']['Nodes'][0]['Facets']:
                            if i['IsSelected'] is True:
                                for model in i['Refinements']['Nodes'][0]['Facets']:
                                    if model['IsSelected'] is True:
                                        for generation in model['Refinements']['Nodes'][0]['Facets']:
                                            if generation['IsSelected'] is True:
                                                if generation['Refinements']['Nodes']:
                                                    for modification in generation['Refinements']['Nodes'][0]['Facets']:
                                                        if not modification['Expression'].startswith('YearGroup.'):
                                                            modifications.append(
                                                                {
                                                                    'code': modification['Metadata']['Code'][0],
                                                                    'action': modification['Action'],
                                                                    'display_value': modification['DisplayValue'],
                                                                    'generation_id': generation_id
                                                                }
                                                            )
                                                    break
                                        break
                                break
                        break
                break

    async with get_db() as session:
        modification_repo = ModificationRepository(session)
        await modification_repo.update_modifications(modifications)


async def insert_configurations():
    async with get_db() as session:
        modification_repo = ModificationRepository(session)
        modifications: list[tuple] = await modification_repo.get_all_modification_actions()

    configurations = []
    for modification_id, action in modifications:
        try:
            async with AsyncHTTPClient('https://example') as client:
                configurations_data = await client.get(
                    endpoint='/endpoint',
                    params={
                        'param': 'example',
                    }
                )
        except Exception as e:
            logger.error(f'Ошибка получение конфигурации модификации ({modification_id}): {str(e)}')
            continue

        for node in configurations_data['iNav']['Nodes']:
            if node['Name'] == 'CarType':
                for facet in node['Facets']:
                    if facet['IsSelected'] is True:
                        for i in facet['Refinements']['Nodes'][0]['Facets']:
                            if i['IsSelected'] is True:
                                for model in i['Refinements']['Nodes'][0]['Facets']:
                                    if model['IsSelected'] is True:
                                        for generation in model['Refinements']['Nodes'][0]['Facets']:
                                            if generation['IsSelected'] is True:
                                                if generation['Refinements']['Nodes']:
                                                    for modification in generation['Refinements']['Nodes'][0]['Facets']:
                                                        if modification['IsSelected'] and not modification['Expression'].startswith('YearGroup.'):
                                                            for configuration in modification['Refinements']['Nodes'][0]['Facets']:
                                                                configurations.append(
                                                                    {
                                                                        'code': configuration['Metadata']['Code'][0],
                                                                        'action': configuration['Action'],
                                                                        'display_value': configuration['DisplayValue'],
                                                                        'modification_id': modification_id,
                                                                        'count': configuration['Count']
                                                                    }
                                                                )
                                                            break
                                                    break
                                        break
                                break
                        break
                break

    async with get_db() as session:
        configuration_repo = ConfigurationRepository(session)

        while len(configurations) >= 4_000:
            await configuration_repo.update_configurations(configurations[:4_000])
            configurations = configurations[4_000:]

        if configurations:
            await configuration_repo.update_configurations(configurations)


async def daily_parsing_task():
    logger.info('Запуск ежедневной задачи парсинга')

    logger.info('Запущен процесс парсинга сайта encar')

    try:
        logger.info('Начало парсинга брендов...')
        await insert_brands()
        logger.info('Парсинг брендов завершен')
    except Exception as e:
        logger.error(f'Ошибка парсинга брендов: {str(e)}')

    try:
        logger.info('Начало парсинга моделей...')
        await insert_models()
        logger.info('Парсинг моделей завершен')
    except Exception as e:
        logger.error(f'Ошибка парсинга моделей:{str(e)}')

    try:
        logger.info('Начало парсинга поколений...')
        await insert_generations()
        logger.info('Парсинг поколений завершен')
    except Exception as e:
        logger.error(f'Ошибка парсинга поколений:{str(e)}')

    try:
        logger.info('Начало парсинга модификаций...')
        await insert_modifications()
        logger.info('Парсинг модификаций завершен')
    except Exception as e:
        logger.error(f'Ошибка парсинга модификаций:{str(e)}')

    try:
        logger.info('Начало парсинга конфигураций...')
        await insert_configurations()
        logger.info('Парсинг конфигураций завершен')
    except Exception as e:
        logger.error(f'Ошибка парсинга конфигураций:{str(e)}')

    logger.info(f'Парсинг завершен')
    
    logger.info('Ежедневный задача парсинга выполнен')
