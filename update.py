import ast, sqlite3
src = open('swh.py').read()
def rep(old, new, label, all_=False):
    global src
    if old in src:
        src = src.replace(old, new) if all_ else src.replace(old, new, 1)
        print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Таблица камер
conn = sqlite3.connect('switch_replacements.db')
conn.execute('''CREATE TABLE IF NOT EXISTS cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER, side TEXT, model TEXT, serial TEXT,
    ip TEXT, mac TEXT, zone TEXT, notes TEXT, config_text TEXT)''')
conn.commit()
conn.close()
print('ok: таблица cameras')

# 2) Тип наряда «Замена камеры»
rep('<option value="service">🔧 Сервис / ремонт</option>',
    '<option value="service">🔧 Сервис / ремонт</option>\n                    <option value="camera">📹 Замена камеры</option>',
    'тип наряда: камера')
rep("order.order_type==='new'?'🆕 новая установка':order.order_type==='service'?'🔧 сервис':'🔄 замена'",
    "order.order_type==='new'?'🆕 новая установка':order.order_type==='service'?'🔧 сервис':order.order_type==='camera'?'📹 камера':'🔄 замена'",
    'бейдж типа: камера', all_=True)

# 3) Секция камер на странице наряда
if 'id="camsBox"' not in src:
    rep('<h3>📚 Команды и ресурсы</h3>',
"""<h3>📹 Камеры (замена / конфигурация)</h3>
<div style="background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;">
    <div id="camsBox"></div>
    <button class="btn btn-secondary" onclick="addCam('old')">+ Старая камера</button>
    <button class="btn btn-secondary" onclick="addCam('new')">+ Новая камера</button>
</div>
<h3>📚 Команды и ресурсы</h3>""", 'секция камер на наряде')
    rep('refreshOrderHeader();', 'refreshOrderHeader();\nloadCams();', 'вызов loadCams')

# 4) JS камер в common.js
import os
ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'function loadCams' not in ajs:
    ajs += '''
function camCard(c){
  var side=c.side==='old'?'СТАРНАЯ':'НОВАЯ';
  return '<div style="border:1px solid #ddd;border-radius:8px;padding:.8rem;margin:.5rem 0;" data-cam="'+c.id+'">'
   +'<b>📹 '+side+' камера</b> '
   +'<button class="btn btn-danger" style="padding:2px 8px;" onclick="delCam('+c.id+')">🗑</button>'
   +'<div class="form-row">'
   +'<div class="form-group"><label>Модель:</label><input class="camModel" value="'+(c.model||'')+'" placeholder="Beward BR-2.4 и т.п."></div>'
   +'<div class="form-group"><label>Серийник:</label><input class="camSerial" value="'+(c.serial||'')+'"></div>'
   +'<div class="form-group"><label>IP / ID:</label><input class="camIp" value="'+(c.ip||'')+'"></div>'
   +'</div>'
   +'<div class="form-row">'
   +'<div class="form-group"><label>MAC:</label><input class="camMac" value="'+(c.mac||'')+'"></div>'
   +'<div class="form-group"><label>Зона / надпись:</label><input class="camZone" value="'+(c.zone||'')+'" placeholder="безопасный регион, надпись..."></div>'
   +'</div>'
   +'<div class="form-group"><label>Примечания:</label><input class="camNotes" value="'+(c.notes||'')+'"></div>'
   +'<div class="form-group"><label>Конфиг (экспорт/импорт):</label><textarea class="camCfg" style="width:100%;height:90px;font-family:monospace;">'+(c.config_text||'')+'</textarea></div>'
   +'<button class="btn btn-primary" onclick="saveCam('+c.id+')">💾 Сохранить</button> '
   +'<button class="btn btn-secondary" onclick="exportCam('+c.id+')">📤 Экспорт конфига</button> '
   +'<button class="btn btn-secondary" onclick="importCam('+c.id+')">📥 Импорт конфига</button>'
   +'</div>';
}
function loadCams(){
  var box=document.getElementById('camsBox');
  if(!box) return;
  fetch('/api/cameras?order_id='+orderId).then(function(r){return r.json();}).then(function(rows){
    box.innerHTML=rows.map(camCard).join('')||'<small>Камер в наряде пока нет.</small>';
  });
}
function addCam(side){
  fetch('/api/cameras',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({order_id:orderId, side:side})}).then(loadCams);
}
function saveCam(id){
  var d=document.querySelector('[data-cam="'+id+'"]');
  var body={model:d.querySelector('.camModel').value, serial:d.querySelector('.camSerial').value,
    ip:d.querySelector('.camIp').value, mac:d.querySelector('.camMac').value,
    zone:d.querySelector('.camZone').value, notes:d.querySelector('.camNotes').value,
    config_text:d.querySelector('.camCfg').value};
  fetch('/api/cameras/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(){alert('Сохранено');});
}
function delCam(id){
  if(!confirm('Удалить камеру?')) return;
  fetch('/api/cameras/'+id,{method:'DELETE'}).then(loadCams);
}
function exportCam(id){
  fetch('/api/cameras/'+id).then(function(r){return r.json();}).then(function(c){
    var NL=String.fromCharCode(10);
    var txt='КАМЕРА '+(c.side||'')+NL+'Модель: '+(c.model||'')+NL+'Серийник: '+(c.serial||'')+NL+'IP/ID: '+(c.ip||'')+NL+'MAC: '+(c.mac||'')+NL+'Зона: '+(c.zone||'')+NL+'Примечания: '+(c.notes||'')+NL+NL+'КОНФИГ:'+NL+(c.config_text||'');
    var b=new Blob([txt],{type:'text/plain'});
    var a=document.createElement('a');
    a.href=URL.createObjectURL(b);
    a.download='camera_'+(c.model||'cam')+'_'+(c.serial||id)+'.txt';
    a.click();
  });
}
function importCam(id){
  var inp=document.createElement('input');
  inp.type='file';
  inp.onchange=function(){
    var f=inp.files[0];
    if(!f) return;
    var r=new FileReader();
    r.onload=function(){
      var d=document.querySelector('[data-cam="'+id+'"]');
      d.querySelector('.camCfg').value=r.result;
      alert('Конфиг загружен в поле. Не забудьте 💾 Сохранить');
    };
    r.readAsText(f);
  };
  inp.click();
}
'''
    open(ajs_path, 'w').write(ajs)
    print('ok: common.js + функции камер')

# 5) Эндпоинты камер
if "'/api/cameras'" not in src:
    ep = '''
@app.route('/api/cameras', methods=['GET', 'POST'])
def cameras_api():
    conn = get_db()
    if request.method == 'GET':
        oid = request.args.get('order_id')
        rows = conn.execute('SELECT * FROM cameras WHERE order_id=? ORDER BY side, id', (oid,)).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    d = request.json or {}
    c = conn.cursor()
    c.execute('INSERT INTO cameras (order_id, side, model, serial, ip, mac, zone, notes, config_text) VALUES (?,?,?,?,?,?,?,?,?)',
        (d.get('order_id'), d.get('side', 'new'), d.get('model', ''), d.get('serial', ''),
         d.get('ip', ''), d.get('mac', ''), d.get('zone', ''), d.get('notes', ''), d.get('config_text', '')))
    conn.commit()
    i = c.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': i})

@app.route('/api/cameras/<int:cam_id>', methods=['GET', 'PUT', 'DELETE'])
def camera_api(cam_id):
    conn = get_db()
    if request.method == 'GET':
        r = conn.execute('SELECT * FROM cameras WHERE id=?', (cam_id,)).fetchone()
        conn.close()
        if not r:
            return jsonify({'error': 'nf'}), 404
        return jsonify(dict(r))
    if request.method == 'DELETE':
        conn.execute('DELETE FROM cameras WHERE id=?', (cam_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    d = request.json or {}
    sets = []
    vals = []
    for f in ('model', 'serial', 'ip', 'mac', 'zone', 'notes', 'config_text', 'side'):
        if f in d:
            sets.append(f + '=?')
            vals.append(d[f])
    if sets:
        vals.append(cam_id)
        conn.execute('UPDATE cameras SET ' + ','.join(sets) + ' WHERE id=?', vals)
        conn.commit()
    conn.close()
    return jsonify({'success': True})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    print('ok: эндпоинты камер')

# 6) Камеры в отчёте
rep("    L.append('')\n    L.append('НАПОМИНАНИЯ:')",
"""    conn2 = get_db()
    cams = conn2.execute('SELECT * FROM cameras WHERE order_id=? ORDER BY side', (order_id,)).fetchall()
    conn2.close()
    if cams:
        L.append('')
        L.append('КАМЕРЫ:')
        for c in cams:
            L.append('  %s: %s | серийник %s | IP/ID %s | MAC %s | зона: %s' % (
                'СТАР' if c['side'] == 'old' else 'НОВ', c['model'] or '?', c['serial'] or '—',
                c['ip'] or '—', c['mac'] or '—', c['zone'] or '—'))
    L.append('')
    L.append('НАПОМИНАНИЯ:')""", 'камеры в отчёте')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')