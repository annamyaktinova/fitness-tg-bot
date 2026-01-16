import asyncio
import aiohttp
from config import WEATHER_API_KEY

async def get_temperature(city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['main']['temp']
                else:
                    print(f"Ошибка API: {response.status}, {await response.text()}")
        except aiohttp.ClientError as e:
            print(f"Ошибка клиента API: {e}")
        except asyncio.TimeoutError:
            print("Ошибка: Таймаут при запросе к API")
    return None

async def get_food_info(product_name: str):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product_name}&json=true"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    products = data.get('products', [])
                    if products:
                        first_product = products[0]
                        return {
                            'name': first_product.get('product_name', 'Неизвестно'),
                            'calories': first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
                        }
                    return None
                else:
                    print(f"Ошибка API: {response.status}, {await response.text()}")
        except aiohttp.ClientError as e:
            print(f"Ошибка клиента API: {e}")
        except asyncio.TimeoutError:
            print("Ошибка: Таймаут при запросе к API")
    return None