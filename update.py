import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# ========== 1) VISION: автозаполнение из скриншота биллинга ==========
if "'/api/vision'" not in src:
    ep = '''
@app.route('/api/vision', methods=['POST'])
def vision_api():
    import base64
    import json as _json
    import urllib.request
    pin = request.form.get('pin') or (request.json or {}).get('pin')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'нет файла'}), 400
    b64 = base64.b64encode(f.read()).decode()
    try:
        r = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=10)
        tags = [m.get('name', '') for m in _json.loads(r.read().decode()).get('models', [])]
    except Exception:
        return jsonify({'error': 'ollama недоступна'}), 503
    model = next((t for t in tags if 'vl' in t.lower() or 'llava' in t.lower()), None)
    if not model:
        return jsonify({'error': 'нет зрячей модели (нужна qwen2.5vl или llava)'}), 503
    prompt = ('Извлеки данные со скриншота (биллинг, карточка камеры, табличка). '
              'Верни СТРОГО JSON без пояснений, ключи: login,password,ip,port,vlan,address,mac,rtsp,model,serial,name. '
              'Отсутствующие значения - пустая строка.')
    body = _json.dumps({'model': model, 'prompt': prompt, 'images': [b64], 'stream': False}).encode()
    rq = urllib.request.Request('http://localhost:11434/api/generate', data=body, headers={'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(rq, timeout=300)
        text = _json.loads(r.read().decode()).get('response', '')
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 500
    t = text.strip()
    if t.startswith('```'):
        t = t.split('```')[1]
        if t.startswith('json'):
            t = t[4:]
    data = None
    try:
        data = _json.loads(t)
    except Exception:
        i = t.find('{'); j = t.rfind('}')
        if i >= 0 and j > i:
            try:
                data = _json.loads(t[i:j+1])
            except Exception:
                data = None
    if data is None:
        return jsonify({'error': 'модель не дала JSON', 'raw': text[:500]}), 502
    return jsonify({'ok': True, 'data': data})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    print('ok: /api/vision')

# ========== 2) FDB со свитча по SNMP ==========
if "'/api/fdb_fetch'" not in src:
    ep = '''
@app.route('/api/fdb_fetch', methods=['POST'])
def fdb_fetch():
    import subprocess
    import re as _re
    d = request.json or {}
    ip = d.get('ip', '')
    community = d.get('community', 'public')
    order_id = d.get('order_id')
    side = d.get('side', 'old')
    if not ip or not order_id:
        return jsonify({'error': 'нужны ip и order_id'}), 400
    try:
        p = subprocess.run(['snmpwalk', '-v2c', '-c', community, ip, '1.3.6.1.2.1.17.7.1.2.2.1.2'],
                           capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return jsonify({'error': 'на сервере нет snmpwalk. Установите: apt-get install -y snmp'}), 503
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 500
    if p.returncode != 0:
        return jsonify({'error': 'snmpwalk: ' + (p.stderr or p.stdout)[:300]}), 502
    rows = []
    for line in p.stdout.splitlines():
        m = _re.search(r'\\.1\\.2\\.2\\.1\\.2\\.(\\d+)((?:\\.\\d+){6})\\s+=\\s+INTEGER:\\s*(\\d+)', line)
        if m:
            vlan = m.group(1)
            hx = ''.join('%02X' % int(x) for x in m.group(2).strip('.').split('.'))
            mac = ':'.join(hx[i:i+2] for i in range(0, 12, 2))
            rows.append((int(m.group(3)), vlan, mac))
    if not rows:
        return jsonify({'error': 'FDB пуста или неверный community', 'out': p.stdout[:300]}), 502
    conn = get_db()
    conn.execute("DELETE FROM fdb_tables WHERE order_id=? AND switch_type=?", (order_id, side))
    for port, vlan, mac in rows:
        conn.execute('INSERT INTO fdb_tables (order_id, switch_type, port, vlan, mac_address, subscriber) VALUES (?,?,?,?,?,?)',
                     (order_id, side, port, vlan, mac, ''))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'count': len(rows)})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    print('ok: /api/fdb_fetch')

# ========== 3) ПОЛЕВОЙ РЕЖИМ ==========
if "'/field'" not in src:
    FIELD = '''FIELD_LIST_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Полевой режим</title>
<style>body{font-family:Arial;font-size:18px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:16px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
a.btn{display:block;background:#3498db;color:#fff;padding:14px;border-radius:8px;text-decoration:none;text-align:center;font-size:20px;margin:8px 0;}
.big{font-size:22px;font-weight:600;} label.step{display:block;background:#fff;margin:8px;padding:14px;border-radius:10px;font-size:19px;}
input[type=checkbox]{width:28px;height:28px;vertical-align:middle;margin-right:10px;}
.ph{width:110px;height:85px;object-fit:cover;border-radius:6px;margin:4px;}</style></head>
<body><div class="card big">📱 Полевой режим — открытые наряды</div>
{% for o in orders %}<div class="card"><div class="big">Наряд {{ o.order_number }}</div>
<div>{{ o.old_switch_ip or '—' }} → {{ o.new_switch_ip or '—' }}</div>
<div>{{ o.old_switch_location or o.new_switch_location or '' }}</div>
<a class="btn" href="/field/{{ o.id }}">Открыть ▶</a></div>{% endfor %}
</body></html>"""

FIELD_ORDER_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Наряд {{ o.order_number }} — полевой</title>
<style>body{font-family:Arial;font-size:18px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:16px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
a.btn{display:inline-block;background:#3498db;color:#fff;padding:12px;border-radius:8px;text-decoration:none;font-size:18px;margin:6px 4px 6px 0;}
.big{font-size:22px;font-weight:600;} label.step{display:block;background:#fff;margin:8px;padding:14px;border-radius:10px;font-size:19px;}
input[type=checkbox]{width:28px;height:28px;vertical-align:middle;margin-right:10px;}
.ph{width:110px;height:85px;object-fit:cover;border-radius:6px;margin:4px;}</style></head>
<body>
<div class="card big">📱 Наряд {{ o.order_number }}</div>
<div class="card">
<div><b>Адрес:</b> {{ o.old_switch_location or o.new_switch_location or '—' }}</div>
<div><b>Старый:</b> {{ o.old_switch_ip or '—' }} ({{ o.old_switch_model or '—' }})</div>
<div><b>Новый:</b> {{ o.new_switch_ip or '—' }} ({{ o.new_switch_model or '—' }})</div>
<a class="btn" href="/passport/{{ o.id }}" target="_blank">🖨️ Паспорт</a>
<a class="btn" href="/field">← Список</a>
</div>
<div class="card big">✅ Этапы</div>
{% for s in steps %}<label class="step"><input type="checkbox" {% if s.done or fl.get(loop.index0) %}checked{% endif %} onchange="tgStep({{ s.id }}, this.checked)"> {{ s.step_text }}</label>{% endfor %}
<div class="card big">🔌 Подключения</div>
<div class="card">{% for l in links %}<div>{{ '⬆️' if l.link_type=='uplink' else '⬇️' }} порт {{ l.old_port }} → <b>{{ l.new_port or '??' }}</b> | {{ l.upstream_device }} : {{ l.upstream_port }}</div>{% endfor %}
{% for c in cams %}<div>📹 {{ c.model }}: <a href="{{ c.rtsp }}" target="_blank">поток</a> | {{ c.switch_name }}:{{ c.switch_port }}</div>{% endfor %}
</div>
<div class="card big">📷 Фото ДО</div>
<div class="card"><div id="phBefore"></div><input type="file" accept="image/*" capture="environment" onchange="upF('field_before', this)"></div>
<div class="card big">📷 Фото ПОСЛЕ</div>
<div class="card"><div id="phAfter"></div><input type="file" accept="image/*" capture="environment" onchange="upF('field_after', this)"></div>
<script>
var orderId={{ o.id }};
function tgStep(id, done){
  fetch('/api/steps/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({done:done?1:0})});
}
function upF(type, input){
  var f=input.files[0];
  if(!f) return;
  var fd=new FormData();
  fd.append('file', f);
  fd.append('entity_type', type);
  fd.append('entity_id', orderId);
  fd.append('description', type);
  fetch('/api/attachments',{method:'POST', body:fd}).then(function(){ loadF(type); });
  input.value='';
}
function loadF(type){
  var box=document.getElementById(type==='field_before'?'phBefore':'phAfter');
  fetch('/api/attachments?entity_type='+type+'&entity_id='+orderId).then(function(r){return r.json();}).then(function(rows){
    box.innerHTML=rows.map(function(a){ return '<a href="/uploads/'+a.filename+'" target="_blank"><img class="ph" src="/uploads/'+a.filename+'"></a>'; }).join('');
  });
}
loadF('field_before'); loadF('field_after');
</script>
</body></html>"""

@app.route('/field')
def field_page():
    conn = get_db()
    orders = conn.execute("SELECT * FROM work_orders WHERE status!='closed' ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(FIELD_LIST_HTML, orders=orders)

@app.route('/field/<int:order_id>')
def field_order(order_id):
    conn = get_db()
    o = conn.execute('SELECT * FROM work_orders WHERE id=?', (order_id,)).fetchone()
    if not o:
        conn.close()
        return 'Наряд не найден', 404
    steps = conn.execute('SELECT * FROM order_steps WHERE order_id=? ORDER BY pos', (order_id,)).fetchall()
    links = conn.execute('SELECT * FROM links WHERE order_id=? ORDER BY link_type, old_port', (order_id,)).fetchall()
    try:
        cams = conn.execute('SELECT * FROM cameras WHERE order_id=? ORDER BY side', (order_id,)).fetchall()
    except Exception:
        cams = []
    conn.close()
    return render_template_string(FIELD_ORDER_HTML, o=o, steps=steps, links=links, cams=cams, fl=auto_flags(order_id))


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + FIELD + src[idx:]
    print('ok: полевой режим /field')

rep('<a href="/commands" class="nav-link">📚 Команды</a>',
    '<a href="/commands" class="nav-link">📚 Команды</a>\n            <a href="/field" class="nav-link">📱 Полевой</a>',
    'ссылка Полевой в меню')

# ========== 4) common.js: кнопка 📸 + SNMP-блок на FDB ==========
import os
ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'camFromShot' not in ajs:
    ajs = ajs.replace("""onclick="importCam('+c.id+')">📥 Импорт конфига</button>'""",
"""onclick="importCam('+c.id+')">📥 Импорт конфига</button> '
   +'<button class="btn btn-secondary" onclick="camFromShot('+c.id+')">📸 Из скриншота</button>'""", 1)
    ajs += '''
function camFromShot(id){
  var inp=document.createElement('input');
  inp.type='file'; inp.accept='image/*';
  inp.onchange=function(){
    var f=inp.files[0];
    if(!f) return;
    var fd=new FormData();
    fd.append('file', f);
    fd.append('pin', localStorage.getItem('swhpin')||prompt('PIN:')||'');
    alert('Распознаю скриншот (до минуты)...');
    fetch('/api/vision',{method:'POST', body:fd}).then(function(r){return r.json();}).then(function(res){
      if(!res.data){ alert('Ошибка: '+(res.error||'неизвестно')+(res.raw?' | '+res.raw:'')); return; }
      var d=res.data;
      var c=document.querySelector('[data-cam="'+id+'"]');
      if(!c) return;
      function set(cls, v){ if(v){ var el=c.querySelector(cls); if(el){ el.value=v; } } }
      set('.camLogin', d.login); set('.camPass', d.password); set('.camIp', d.ip);
      set('.camPort', d.port); set('.camVlan', d.vlan); set('.camMac', d.mac);
      set('.camRtsp', d.rtsp); set('.camModel', d.model); set('.camSerial', d.serial);
      set('.camZone', d.address); set('.camNotes', d.name);
      alert('Поля заполнены! Проверьте и нажмите 💾 Сохранить');
    }).catch(function(e){ alert('Ошибка: '+e.message); });
  };
  inp.click();
}
function fetchFdb(){
  var el=document.getElementById('fdbIp');
  var body={order_id:parseInt(el.dataset.order), ip:el.value,
    community:document.getElementById('fdbCom').value,
    side:document.getElementById('fdbSide').value};
  document.getElementById('fdbMsg').textContent='Снимаю FDB...';
  fetch('/api/fdb_fetch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  .then(function(r){return r.json();}).then(function(res){
    document.getElementById('fdbMsg').textContent=res.ok? ('Готово: '+res.count+' записей') : ('Ошибка: '+res.error);
    if(res.ok){ setTimeout(function(){ location.reload(); }, 1200); }
  });
}
document.addEventListener('DOMContentLoaded', function(){
  if(location.pathname.indexOf('/fdb/')===0){
    var c=document.querySelector('.container');
    if(c){
      var d=document.createElement('div');
      d.style.cssText='background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;';
      d.innerHTML='<b>🧲 Снять FDB со свитча (SNMP)</b><br>IP: <input id="fdbIp" style="width:140px;"> Community: <input id="fdbCom" value="public" style="width:100px;"> Сторона: <select id="fdbSide"><option value="old">ДО</option><option value="new">ПОСЛЕ</option></select> <button class="btn btn-primary" onclick="fetchFdb()">Снять</button> <span id="fdbMsg"></span>';
      c.insertBefore(d, c.firstChild);
      var m=location.pathname.match(/\\/fdb\\/(\\d+)/);
      if(m){
        document.getElementById('fdbIp').dataset.order=m[1];
        fetch('/api/orders/'+m[1]).then(function(r){return r.json();}).then(function(o){
          document.getElementById('fdbIp').value=o.old_switch_ip||'';
        });
      }
    }
  }
});
'''
    open(ajs_path, 'w').write(ajs)
    print('ok: common.js 📸 + SNMP')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')