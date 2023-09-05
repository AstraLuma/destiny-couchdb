import asyncio
import os

# from destiny_couchdb import client, manifest
#
#
# async def main():
#     async with client.Bungie(os.environ['BUNGIE_KEY']) as bungo:
#         mani = await manifest.get_manifest(bungo)
#         world = await mani.get_world_json()
#         print(world.keys())
#

from destiny_couchdb import main
asyncio.run(main())
