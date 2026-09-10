import ast, sqlite3
src = open('swh.py').read()
def rep(old, new, label, all_=False):
    global src
    if old in src:
        src = src.replace(old, new) if all_ else src.replace(old, new, 1)
        print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Камера: на каком свитче и в каком порту стоит
conn = sqlite3.connect('switch_replacements.db')
for col in ('switch_name', 'switch_port'):
    try:
        conn.execute('ALTER TABLE cameras ADD COLUMN ' + col + ' TEXT')
        print('  ok: cameras.' + col)
    except Exception:
        print('  уже есть: cameras.' + col)
conn.commit()
conn.close()

import os
ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'camSwitch' not in ajs:
    ajs = ajs.replace("""   +'<div class="form-group"><label>RTSP-поток:</label>""",
"""   +'<div class="form-row">'
   +'<div class="form-group"><label>Свитч (где стоит):</label><select class="camSwitch"></select></div>'
   +'<div class="form-group"><label>Порт свитча:</label><input class="camSwitchPort" style="width:90px;" value="'+(c.switch_port||'')+'"></div>'
   +'</div>'
   +'<div class="form-group"><label>RTSP-поток:</label>""", 1)
    ajs = ajs.replace("""    rows.forEach(function(r){ loadAttachments('camera', r.id, 'camFiles_'+r.id); });""",
"""    rows.forEach(function(r){
      loadAttachments('camera', r.id, 'camFiles_'+r.id);
      var sel=document.querySelector('[data-cam="'+r.id+'"] .camSwitch');
      if(sel){
        devList().then(function(ds){
          var html='<option value="">— выберите свитч —</option>'+ds.map(function(d){
            return '<option value="'+d.name+'">'+d.name+' · '+(d.ip_address||'')+' · 📍 '+(d.location||'—')+'</option>';
          }).join('');
          var ex=r.switch_name && !ds.some(function(d){ return d.name===r.switch_name; });
          if(ex){ html+='<option value="'+r.switch_name+'">'+r.switch_name+' (текущий)</option>'; }
          sel.innerHTML=html;
          sel.value=r.switch_name||'';
        });
      }
    });""", 1)
    ajs = ajs.replace("""    rtsp:d.querySelector('.camRtsp').value, vlan:d.querySelector('.camVlan').value,""",
"""    rtsp:d.querySelector('.camRtsp').value, vlan:d.querySelector('.camVlan').value,
    switch_name:(d.querySelector('.camSwitch')||{}).value||'', switch_port:d.querySelector('.camSwitchPort').value,""", 1)
    open(ajs_path, 'w').write(ajs)
    print('ok: камера привязана к свитчу и порту')
else:
    print('привязка к свитчу уже есть')

rep("for f in ('model', 'serial', 'ip', 'mac', 'zone', 'notes', 'config_text', 'side', 'login', 'password', 'rtsp', 'vlan', 'port'):",
    "for f in ('model', 'serial', 'ip', 'mac', 'zone', 'notes', 'config_text', 'side', 'login', 'password', 'rtsp', 'vlan', 'port', 'switch_name', 'switch_port'):",
    'PUT камер: свитч/порт')

rep("""            if c['rtsp']:
                L.append('      RTSP: %s' % c['rtsp'])""",
"""            if c['rtsp']:
                L.append('      RTSP: %s' % c['rtsp'])
            if c['switch_name'] or c['switch_port']:
                L.append('      стоит на: %s, порт %s' % (c['switch_name'] or '—', c['switch_port'] or '—'))""",
    'отчёт: свитч/порт камеры')

rep('<tr><th></th><th>Модель</th><th>Серийник</th><th>IP/ID</th><th>Логин</th><th>RTSP</th><th>Зона</th></tr>',
    '<tr><th></th><th>Модель</th><th>Серийник</th><th>IP/ID</th><th>Логин</th><th>Свитч:порт</th><th>RTSP</th><th>Зона</th></tr>',
    'паспорт: шапка камер')
rep("<td>{{ c.login or '—' }}</td><td>{{ c.rtsp or '—' }}</td><td>{{ c.zone or '—' }}</td></tr>",
    "<td>{{ c.login or '—' }}</td><td>{{ (c.switch_name or '—') ~ ':' ~ (c.switch_port or '—') }}</td><td>{{ c.rtsp or '—' }}</td><td>{{ c.zone or '—' }}</td></tr>",
    'паспорт: строка камер')

# 2) Номер наряда везде вместо внутреннего id
rep('#{{ order_id }}', '#{{ order_number }}', 'заголовок # наряда', all_=True)
rep('№{{ order_id }}', '№{{ order_number }}', 'заголовок № наряда', all_=True)

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')