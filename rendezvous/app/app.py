import asyncio
import logging
from aiohttp import web

logging.basicConfig()
logger = logging.getLogger('cloudbutton')
logger.setLevel(logging.DEBUG)

routes = web.RouteTableDef()

pools = {}


@routes.get('/pool/{name}')
async def get_pool(request):
    global pools

    try:
        address = request.rel_url.query['address']
        node = request.rel_url.query['node']
    except KeyError as e:
        logger.debug('Bad request, {} required'.format(e))
        return web.json_response({'error': '{} required'.format(e)}, status=400)

    pool_name = request.match_info.get('name', None)
    if pool_name is None:
        logger.debug('Bad request, pool name required')
        return web.json_response({'error': 'pool name required'}, status=400)

    if pool_name not in pools:
        logger.debug('Bad request, pool not registered')
        return web.json_response({'error': 'pool {} not registered'.format(pool_name)}, status=404)

    pool = pools[pool_name]

    if node in pool['members']:
        logger.debug('Bad request, member {} already in pool')
        return web.json_response({'error': 'member {} already in pool'}, status=400)
    
    if address in set(pool['members'].values()):
        return web.json_response({'error': 'member already has address {}'.format(address)}, status=400)

    pool['members'][node] = address
    msg = 'Added {} pool member {} \
        ({}) ({}/{})'.format(pool_name, node, address, len(pool['members']), pool['size'])
    logger.debug(msg)

    if len(pool['members']) >= pool['size']:
        pool['event'].set()
        logger.debug('All members awaited for pool {}'.format(pool_name))
        del pools[pool_name]
    else:
        await pool['event'].wait()

    return web.json_response({'pool': pool['members']}, status=200)


@routes.post('/pool/{name}')
async def register_pool(request):
    global pools

    try:
        size = int(request.rel_url.query['size'])
    except KeyError as e:
        return web.json_response({'error': '{} required'.format(e)}, status=400)

    pool_name = request.match_info.get('name', None)
    if pool_name is None:
        return web.json_response({'error': 'pool name required'}, status=400)

    pool = {'name': pool_name,
            'size': size,
            'members': {},
            'event': asyncio.Event()}

    pools[pool_name] = pool

    logger.debug(pool)

    return web.json_response({'pool': pool_name}, status=200)


@routes.get('/')
async def default(request):
    logger.debug('hola')
    return web.Response(text='hola\n')


if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host='0.0.0.0', port=8080)
