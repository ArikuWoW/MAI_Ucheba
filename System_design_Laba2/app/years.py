from aiohttp import web

app = web.Application()

async def handler_1(request):
    return web.Response(text="Привет!")

async def handler_2(request):
    return web.Response(text="О нас")

async def handler_3(request):
    id = request.match_info['user_id']
    return web.Response(text=f"Ваш id={id}")


app.add_routes([web.get("/", handler_1)])
app.add_routes([web.get("/about", handler_2)])
app.add_routes([web.get("/user/{id}", handler_3)])

if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=8000)

