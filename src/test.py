from flask import Flask, request

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>SCARA Robot Control — Deluxe Edition</title>

  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Roboto:wght@300;400;500&display=swap" rel="stylesheet"/>

  <!-- Font Awesome -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css"/>

  <!-- Chart.js for live plot -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    :root {
      --bg: #0d0d0d;
      --card: #1a1a1a;
      --accent: #00ffcc;
      --accent2: #ff00aa;
      --text: #e0e0e0;
      --text-muted: #888;
      --success: #00ff88;
      --danger: #ff4444;
    }

    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Roboto', sans-serif;
      min-height: 100vh;
      padding: 20px;
      background-image: 
        radial-gradient(circle at 10% 20%, rgba(0,255,204,0.15) 0%, transparent 20%),
        radial-gradient(circle at 90% 80%, rgba(255,0,170,0.15) 0%, transparent 20%);
    }

    .container {
      max-width: 1200px;
      margin: auto;
      display: grid;
      gap: 20px;
      grid-template-columns: 1fr 1fr;
    }

    @media (max-width: 900px) { .container { grid-template-columns: 1fr; } }

    header {
      grid-column: 1 / -1;
      text-align: center;
      padding: 30px 0;
    }
    h1 {
      font-family: 'Orbitron', sans-serif;
      font-size: 3rem;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }
    .subtitle { color: var(--text-muted); font-weight: 300; }

    .card {
      background: var(--card);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
      border: 1px solid rgba(0,255,204,0.2);
      position: relative;
      overflow: hidden;
    }
    .card::before {
      content: '';
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 4px;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
    }

    .section-title {
      font-family: 'Orbitron', sans-serif;
      font-size: 1.4rem;
      margin-bottom: 16px;
      color: var(--accent);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    /* Sliders */
    .slider-group {
      margin: 16px 0;
    }
    .slider-label {
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
      font-size: 0.95rem;
    }
    .slider {
      -webkit-appearance: none;
      width: 100%;
      height: 8px;
      border-radius: 4px;
      background: #333;
      outline: none;
      margin: 8px 0;
    }
    .slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 24px; height: 24px;
      border-radius: 50%;
      background: var(--accent);
      cursor: pointer;
      box-shadow: 0 0 12px rgba(0,255,204,0.6);
      transition: 0.2s;
    }
    .slider::-webkit-slider-thumb:hover { transform: scale(1.15); }

    /* Buttons */
    .btn {
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      color: #000;
      border: none;
      padding: 14px 24px;
      font-weight: 500;
      border-radius: 12px;
      cursor: pointer;
      font-size: 1rem;
      transition: all 0.3s;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin: 6px;
    }
    .btn:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,255,204,0.4); }
    .btn:active { transform: translateY(0); }
    .btn-home { background: #444; color: #fff; }
    .btn-save { background: var(--success); color: #000; }
    .btn-run { background: var(--danger); color: #fff; }

    /* Status */
    .status {
      display: flex;
      justify-content: space-around;
      margin-top: 20px;
      font-family: 'Orbitron', sans-serif;
    }
    .status-item {
      text-align: center;
    }
    .status-value {
      font-size: 1.5rem;
      color: var(--accent);
    }

    /* Plot */
    #plot { height: 300px; margin-top: 20px; }

    /* Log */
    #log {
      background: #111;
      height: 150px;
      overflow-y: auto;
      padding: 12px;
      border-radius: 8px;
      font-family: monospace;
      font-size: 0.85rem;
      color: #0f0;
    }

    /* Footer */
    footer {
      grid-column: 1 / -1;
      text-align: center;
      padding: 30px 0;
      color: var(--text-muted);
      font-size: 0.9rem;
    }
    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>

<div class="container">
  <header>
    <h1>SCARA Robot Control</h1>
    <p class="subtitle">Deluxe Web Interface • Real-time • Beautiful</p>
  </header>

  <!-- Control Panel -->
  <div class="card">
    <div class="section-title"><i class="fas fa-robot"></i> Joint Control</div>

    <div class="slider-group">
      <div class="slider-label">θ1 <span id="t1">90</span>°</div>
      <input type="range" class="slider" id="s1" min="0" max="180" value="90">
    </div>

    <div class="slider-group">
      <div class="slider-label">θ2 <span id="t2">0</span>°</div>
      <input type="range" class="slider" id="s2" min="-90" max="90" value="0">
    </div>

    <div class="slider-group">
      <div class="slider-label">φ (Gripper Rotation) <span id="phi">90</span>°</div>
      <input type="range" class="slider" id="s3" min="0" max="180" value="90">
    </div>

    <div class="slider-group">
      <div class="slider-label">Z Height <span id="z">170</span> mm</div>
      <input type="range" class="slider" id="sz" min="0" max="300" value="170">
    </div>

    <div class="slider-group">
      <div class="slider-label">Gripper <span id="g">90</span>°</div>
      <input type="range" class="slider" id="sg" min="0" max="180" value="90">
    </div>

    <div style="margin-top:24px; text-align:center;">
      <button class="btn" onclick="sendMove()"><i class="fas fa-paper-plane"></i> Go</button>
      <button class="btn btn-home" onclick="home()"><i class="fas fa-home"></i> Home</button>
      <button class="btn btn-save" onclick="savePos()"><i class="fas fa-save"></i> Save</button>
      <button class="btn btn-run" onclick="runSequence()"><i class="fas fa-play"></i> Run</button>
    </div>
  </div>

  <!-- Status & Plot -->
  <div class="card">
    <div class="section-title"><i class="fas fa-chart-line"></i> End Effector</div>
    <div class="status">
      <div class="status-item">
        <div>X</div>
        <div class="status-value" id="x">365</div>
      </div>
      <div class="status-item">
        <div>Y</div>
        <div class="status-value" id="y">0</div>
      </div>
      <div class="status-item">
        <div>Z</div>
        <div class="status-value" id="zVal">170</div>
      </div>
    </div>

    <canvas id="plot"></canvas>

    <div id="log"></div>
  </div>
</div>

<footer>
  Built with <i class="fas fa-heart" style="color:#ff00aa"></i> for <a href="https://howtomechatronics.com/projects/scara-robot-how-to-build-your-own-arduino-based-robot/" target="_blank">HowToMechatronics SCARA</a> • Open Source • 2025
</footer>

<script>
  // Config
  const L1 = 225, L2 = 180; // mm
  const saved = [];
  let chart;

  // Elements
  const sliders = ['s1','s2','s3','sz','sg'];
  const labels = ['t1','t2','phi','z','g'];

  // Init
  document.addEventListener('DOMContentLoaded', () => {
    sliders.forEach((id, i) => {
      const el = document.getElementById(id);
      el.oninput = () => updateLabel(i);
    });
    initChart();
    updateAll();
  });

  function updateLabel(i) {
    const val = document.getElementById(sliders[i]).value;
    document.getElementById(labels[i]).innerText = val;
    if (i < 2) calcFK();
    if (i === 3) document.getElementById('zVal').innerText = val;
  }

  function updateAll() {
    sliders.forEach((_, i) => updateLabel(i));
  }

  function calcFK() {
    const t1 = +document.getElementById('s1').value * 0.0174532925;
    const t2 = +document.getElementById('s2').value * 0.0174532925;
    const x = L1 * Math.cos(t1) + L2 * Math.cos(t1 + t2);
    const y = L1 * Math.sin(t1) + L2 * Math.sin(t1 + t2);
    document.getElementById('x').innerText = Math.round(x);
    document.getElementById('y').innerText = Math.round(y);
    updatePlot(x, y);
  }

  function initChart() {
    const ctx = document.getElementById('plot').getContext('2d');
    chart = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Trajectory',
          data: [{x:365, y:0}],
          borderColor: '#00ffcc',
          backgroundColor: '#ff00aa',
          pointRadius: 6,
          showLine: true,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: { title: { display: true, text: 'X (mm)', color: '#fff' }, grid: { color: '#333' } },
          y: { title: { display: true, text: 'Y (mm)', color: '#fff' }, grid: { color: '#333' } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  function updatePlot(x, y) {
    const data = chart.data.datasets[0].data;
    if (data.length > 50) data.shift();
    data.push({x, y});
    chart.update('quiet');
  }

  // Communication
  function send(cmd, data = {}) {
    fetch(`/${cmd}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(r => r.text()).then(log).catch(log);
  }

  function sendMove() {
    const data = {
      t1: +document.getElementById('s1').value,
      t2: +document.getElementById('s2').value,
      phi: +document.getElementById('s3').value,
      z: +document.getElementById('sz').value,
      g: +document.getElementById('sg').value
    };
    send('move', data);
  }

  function home() { send('home'); }
  function savePos() {
    const pos = {
      t1: +document.getElementById('s1').value,
      t2: +document.getElementById('s2').value,
      phi: +document.getElementById('s3').value,
      z: +document.getElementById('sz').value,
      g: +document.getElementById('sg').value
    };
    saved.push(pos);
    log(`Saved position #${saved.length}`);
  }
  function runSequence() {
    if (!saved.length) return log('No positions saved!');
    log('Running sequence...');
    saved.forEach((pos, i) => {
      setTimeout(() => {
        Object.keys(pos).forEach(k => document.getElementById(sliders[['t1','t2','phi','z','g'].indexOf(k)]).value = pos[k]);
        updateAll();
        send('move', pos);
      }, i * 1500);
    });
  }

  function log(msg) {
    const log = document.getElementById('log');
    const line = document.createElement('div');
    line.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
    log.appendChild(line);
    log.scrollTop = log.scrollHeight;
  }
</script>

</body>
</html>
"""

@app.route('/')
def index():
    return HTML

# Обработка движения робота
@app.route('/move', methods=['POST'])
def move():
    data = request.get_json()
    print("Move command received:", data)
    # Здесь можно добавить управление роботом
    return "OK", 200

@app.route('/home')
def home():
    print("Home command received")
    return "OK", 200

@app.route('/save')
def save():
    print("Save command received")
    return "OK", 200

@app.route('/run')
def run():
    print("Run command received")
    return "OK", 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
