import ast, sqlite3
src = open('swh.py').read()
def rep(old, new, label, all_=False):
    global src
    if old in src:
        src = src.replace(old, new) if all_ else src.replace(old, new, 1)
        print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Колонки камеры: логин, пароль, rtsp, vlan, порт
conn = sqlite3.connect('switch_replacements.db')
for col in ('login', 'password', 'rtsp', 'vlan', 'port'):
    try:
        conn.execute('ALTER TABLE cameras ADD COLUMN ' + col + ' TEXT')
        print('  ok: cameras.' + col)
    except Exception:
        print('  уже есть: cameras.' + col)
conn.commit()
conn.close()

# 2) Режим «камера»: скрыть порты и uplink/downlink в форме наряда
rep('<h3>Uplink подключения</h3>', '<div id="uplinksWrap"><h3>Uplink подключения</h3>', 'обёртка uplink-блока')
rep('<button type="button" class="btn btn-secondary" onclick="addDownlinkField()">+ Добавить downlink</button>',
    '<button type="button" class="btn btn-secondary" onclick="addDownlinkField()">+ Добавить downlink</button></div>',
    'конец обёртки uplink-блока')
rep('<select id="orderType">', '<select id="orderType" onchange="toggleCamMode()">', 'onchange у типа наряда')
if 'function toggleCamMode' not in src:
    rep('function editOrder(id){',
"""function toggleCamMode(){
  var t=document.getElementById('orderType');
  var cam=(t && t.value==='camera');
  ['oldSwitchPorts','newSwitchPorts'].forEach(function(id){
    var el=document.getElementById(id);
    if(el && el.closest('.form-group')){ el.closest('.form-group').style.display=cam?'none':''; }
  });
  var uw=document.getElementById('uplinksWrap');
  if(uw){ uw.style.display=cam?'none':''; }
}
function editOrder(id){""", 'toggleCamMode')
rep("    uplinkCount=0;\n    document.getElementById('createOrderModal').style.display='block';",
    "    uplinkCount=0;\n    toggleCamMode();\n    document.getElementById('createOrderModal').style.display='block';",
    'editOrder: применить режим')
rep("    addUplinkField();\n}", "    addUplinkField();\n    toggleCamMode();\n}", 'showCreateOrderModal: режим')

# 3) Карточка камеры: логин/пароль/rtsp/vlan/порт
import os
ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'camLogin' not in ajs:
    ajs = ajs.replace("""   +'<div class="form-group"><label>Примечания:</label><input class="camNotes" value="'+(c.notes||'')+'"></div>'""",
"""   +'<div class="form-row">'
   +'<div class="form-group"><label>Логин:</label><input class="camLogin" value="'+(c.login||'')+'" placeholder="br-291095"></div>'
   +'<div class="form-group"><label>Пароль:</label><input class="camPass" value="'+(c.password||'')+'"></div>'
   +'<div class="form-group"><label>Порт / VLAN:</label><input class="camPort" value="'+(c.port||'')+'" placeholder="21"> / <input class="camVlan" value="'+(c.vlan||'')+'" placeholder="135"></div>'
   +'</div>'
   +'<div class="form-group"><label>RTSP-поток:</label><input class="camRtsp" value="'+(c.rtsp||'')+'" placeholder="rtsp://admin:pass@ip:554/av0_0"></div>'
   +'<div class="form-group"><label>Примечания:</label><input class="camNotes" value="'+(c.notes||'')+'"></div>'""", 1)
    ajs = ajs.replace("""    zone:d.querySelector('.camZone').value, notes:d.querySelector('.camNotes').value,""",
"""    zone:d.querySelector('.camZone').value, notes:d.querySelector('.camNotes').value,
    login:d.querySelector('.camLogin').value, password:d.querySelector('.camPass').value,
    rtsp:d.querySelector('.camRtsp').value, vlan:d.querySelector('.camVlan').value,
    port:d.querySelector('.camPort').value,""", 1)
    open(ajs_path, 'w').write(ajs)
    print('ok: карточка камеры с логином/rtsp')
else:
    print('карточка камеры уже обновлена')

# 4) PUT камер принимает новые поля
rep("for f in ('model', 'serial', 'ip', 'mac', 'zone', 'notes', 'config_text', 'side'):",
    "for f in ('model', 'serial', 'ip', 'mac', 'zone', 'notes', 'config_text', 'side', 'login', 'password', 'rtsp', 'vlan', 'port'):",
    'PUT камер: новые поля')

# 5) Отчёт и паспорт: логин/rtsp камер
rep("""            L.append('  %s: %s | серийник %s | IP/ID %s | MAC %s | зона: %s' % (
                'СТАР' if c['side'] == 'old' else 'НОВ', c['model'] or '?', c['serial'] or '—',
                c['ip'] or '—', c['mac'] or '—', c['zone'] or '—'))""",
"""            L.append('  %s: %s | серийник %s | IP/ID %s | логин %s | зона: %s' % (
                'СТАР' if c['side'] == 'old' else 'НОВ', c['model'] or '?', c['serial'] or '—',
                c['ip'] or '—', c['login'] or '—', c['zone'] or '—'))
            if c['rtsp']:
                L.append('      RTSP: %s' % c['rtsp'])
            if c['port'] or c['vlan']:
                L.append('      порт %s / VLAN %s' % (c['port'] or '—', c['vlan'] or '—'))""", 'отчёт: логин/rtsp камер')
rep('<tr><th></th><th>Модель</th><th>Серийник</th><th>IP/ID</th><th>MAC</th><th>Зона</th></tr>',
    '<tr><th></th><th>Модель</th><th>Серийник</th><th>IP/ID</th><th>Логин</th><th>RTSP</th><th>Зона</th></tr>', 'паспорт: шапка камер')
rep("<tr><td>{{ 'СТАР' if c.side=='old' else 'НОВ' }}</td><td>{{ c.model or '—' }}</td><td>{{ c.serial or '—' }}</td><td>{{ c.ip or '—' }}</td><td>{{ c.mac or '—' }}</td><td>{{ c.zone or '—' }}</td></tr>",
    "<tr><td>{{ 'СТАР' if c.side=='old' else 'НОВ' }}</td><td>{{ c.model or '—' }}</td><td>{{ c.serial or '—' }}</td><td>{{ c.ip or '—' }}</td><td>{{ c.login or '—' }}</td><td>{{ c.rtsp or '—' }}</td><td>{{ c.zone or '—' }}</td></tr>",
    'паспорт: строка камер')

# 6) Страница наряда типа «камера»: скрыть uplink/downlink
rep("    if(order.order_type==='new'){",
"""    if(order.order_type==='camera'){
      ['uplinksList','downlinksList'].forEach(function(id){
        var el=document.getElementById(id);
        if(el){ if(el.previousElementSibling){ el.previousElementSibling.style.display='none'; } el.style.display='none'; }
      });
    }
    if(order.order_type==='new'){""", 'наряд-камера: скрыть uplink/downlink')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')