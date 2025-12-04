from features.api.service import DeezerAPIService
from pprint import pprint

async def main(q: str):
    deezer_api = DeezerAPIService()
    result = await deezer_api.get_artist_albums(q)
    pprint(result)

if __name__ == "__main__":
    query = input("Nombre: ")
    import asyncio
    asyncio.run(main(query))
   