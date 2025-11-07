import uasyncio as asyncio
import ujson as json
from microdot import Microdot, Response
import test2  # твои Stepper и Portal

# --- Настройка ESP портала ---
m2 = test2.Stepper(step_pin=16, dir_pin=4, en_pin=2, sw_pin=33, limit_coord_cm=90)
m1 = test2.Stepper(step_pin=14, dir_pin=15, en_pin=13, sw_pin=27, limit_coord_cm=60)
m1.freq = 20_000
m2.freq = 20_000
p = test2.Portal(m2, m1)
p.enable(True)

STEP = 5

app = Microdot()
Response.default_content_type = 'text/html'

# --- Маршруты ---
@app.route('/')
async def index(request):
    with open('index.html', 'r') as f:
        return f.read()

@app.route('/style.css')
async def css(request):
    with open('style.css', 'r') as f:
        return Response(f.read(), content_type='text/css')

@app.route('/misc/<filename>')
async def misc(request, filename):
    try:
        with open('misc/' + filename, 'rb') as f:
            if filename.endswith('.svg'): ctype = 'image/svg+xml'
            elif filename.endswith('.png'): ctype = 'image/png'
            else: ctype = 'application/octet-stream'
            return Response(f.read(), content_type=ctype)
    except:
        return 'Not found', 404

@app.route('/press', methods=['POST'])
async def press(request):
    data = request.json
    dir = data.get('dir', '').upper()
    value = data.get('value', None)

    global STEP
    if dir == 'UP': p.y += STEP
    elif dir == 'DOWN': p.y -= STEP
    elif dir == 'RIGHT': p.x += STEP
    elif dir == 'LEFT': p.x -= STEP
    elif dir == 'HOME': p.home()
    elif dir == 'STOP': p.enable(False)
    elif dir == 'ZERO' and value:
        x, y = value
        p |= (x, y)
    elif dir == 'SPEED' and value:
        p.x.freq = value
        p.y.freq = value
    return 'OK'

@app.route('/coords')
async def coords(request):
    x, y = p.coord
    return json.dumps({'x': x, 'y': y})

# --- Запуск сервера ---
asyncio.run(app.start_server(host='0.0.0.0', port=80))
