import aiofiles
import csv
import json
from aivc.config.config import L
from aivc.common import ip

async def get_city(text: str) -> str:
    try:
        suffixes = ['市', '省', '自治区', '特别行政区', '地区', '盟', 
                   '州', '县']
        
        zh_to_en_file = "aivc/data/zh_to_en.json"
        async with aiofiles.open(zh_to_en_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            zh_to_en_dict = json.loads(content)
            
        for city_name in zh_to_en_dict:
            clean_city = city_name
            for suffix in suffixes:
                clean_city = clean_city.replace(suffix, '')
                
            if clean_city in text:
                return city_name
                
        return ""
        
    except Exception as e:
        L.error(f"Failed to extract city name from text: {str(e)}")
        return ""
  

async def zh_location_to_en(zh_text: str) -> str:
    try:
        zh_to_en_file = "aivc/data/zh_to_en.json"
        async with aiofiles.open(zh_to_en_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            zh_to_en_dict = json.loads(content)
            en_text = zh_to_en_dict.get(zh_text)
            if en_text: 
                return en_text.split(' ')[0]
    except Exception as e:
        L.error(f"转换中文到英文失败: {str(e)}")
        return zh_text

async def get_city_location(city_name: str) -> ip.IPLocation | None:
    city_name_en = await zh_location_to_en(city_name)
    L.debug(f"get_city_location city_name:{city_name} city_name_en: {city_name_en}")
    file = "aivc/data/World_Cities_Location.csv"
    try:
        async with aiofiles.open(file, mode='r', encoding='utf-8') as f:
            content = await f.read()
            reader = csv.reader(content.splitlines(), delimiter=';')
            for row in reader:
                row = [item.strip('"') for item in row]
                if row[2].lower() == city_name_en.lower():
                    # 返回经度和纬度
                    return ip.IPLocation(
                        city=city_name,
                        lon=float(row[4]),
                        lat=float(row[3])
                    )
    except Exception as e:
        print(f"Error reading city location: {e}")
        return None
    
    return None

if __name__ == "__main__":
    import asyncio
    
    async def main():
        city_name = await get_city("洛阳天气怎么样")
        print("city name:", city_name)
        location = await get_city_location(city_name)
        print(location)
    
    asyncio.run(main())