import ast, sqlite3
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

conn = sqlite3.connect('switch_replacements.db')
for tbl, col, typ in (('work_orders', 'order_type', "TEXT DEFAULT 'replace'"),
                      ('work_orders', 'new_switch_location', 'TEXT'),
                      ('switch_inventory', 'location', 'TEXT')):
    try:
        conn.execute('ALTER TABLE ' + tbl + ' ADD COLUMN ' + col + ' ' + typ)
        print('  ok: колонка', tbl + '.' + col)
    except Exception:
        print('  колонка уже есть:', tbl + '.' + col)
conn.commit()
conn.close()

rep('''            <div class="form-group">
                <label>Номер наряда:</label>
                <input type="text" id="orderNumber" required>
            </div>''',
'''            <div class="form-group">
                <label>Номер наряда:</label>
                <input type="text" id="orderNumber" required>
            </div>
            <div class="form-group">
                <label>Тип наряда:</label>
                <select id="orderType">
                    <option value="replace">🔄 Замена коммутатора</option>
                    <option value="new">🆕 Новая установка (без старого)</option>
                    <option value="service">🔧 Сервис / ремонт</option>
                </select>
            </div>''', 'тип наряда в форме')

rep('''<input type="number" id="newSwitchPorts" value="28">
                </div>
            </div>''',
'''<input type="number" id="newSwitchPorts" value="28">
                </div>
            </div>
            <div class="form-group">
                <label>Адрес нового коммутатора:</label>
                <input type="text" id="newSwitchLocation" placeholder="Где стоит / будет стоять">
            </div>''', 'адрес нового в форме')

rep("new_switch_ports: document.getElementById('newSwitchPorts').value",
"""new_switch_ports: document.getElementById('newSwitchPorts').value,
        order_type: document.getElementById('orderType').value,
        new_switch_location: document.getElementById('newSwitchLocation').value""", 'поля в orderData')

rep("<p><strong>Адрес:</strong> ${order.old_switch_location || 'Не указан'}</p>",
"""<p><strong>Тип:</strong> ${order.order_type==='new'?'🆕 новая установка':order.order_type==='service'?'🔧 сервис':' замена'}</p>
                    <p><strong>Адрес:</strong> ${order.new_switch_location || order.old_switch_location || 'Не указан'}</p>""", 'карточка: тип+адрес')

rep("""        conn.commit()
    conn.close()
    return jsonify({'success': True, 'order_id': order_id})""",
"""        conn.commit()
    cur.execute('UPDATE work_orders SET order_type=?, new_switch_location=? WHERE id=?',
        (data.get('order_type', 'replace'), data.get('new_switch_location', ''), order_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'order_id': order_id})""", 'upsert: тип+адрес')

rep("'commands_used','vehicle_needed'):",
    "'commands_used','vehicle_needed','order_type','new_switch_location'):", 'PUT наряда: новые поля')

rep("<p><strong>Портов:</strong> ${order.new_switch_ports}</p>",
"""<p><strong>Портов:</strong> ${order.new_switch_ports}</p>
                        <p><strong>Адрес:</strong> ${order.new_switch_location || '—'}</p>""", 'наряд: адрес нового')

rep('<div class="form-group"><label>Портов:</label><input type="number" id="devicePorts" value="28"></div>',
'''<div class="form-group"><label>Портов:</label><input type="number" id="devicePorts" value="28"></div>
            <div class="form-group"><label>Адрес:</label><input type="text" id="deviceLocation" placeholder="Где стоит"></div>''', 'карта: поле адреса')

rep("""    await fetch('/api/network-map',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    closeDeviceModal(); loadMap();""",
"""    var r=await fetch('/api/network-map',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    var j=await r.json();
    if(j && j.id){
      await fetch('/api/network-map/'+j.id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:document.getElementById('deviceLocation').value})});
    }
    closeDeviceModal(); loadMap();""", 'карта: сохранение адреса')

rep("<div class=\"sw-model\">${dev.model||'—'} · портов: ${n}</div>",
"""<div class="sw-model">${dev.model||'—'} · портов: ${n}</div>
        <div class="sw-model">📍 ${dev.location||'адрес не указан'}</div>""", 'панель свитча: адрес')

rep("<small>· ${dev.model||''} · портов: ${dev.total_ports||24}</small>",
    "<small>· ${dev.model||''} · портов: ${dev.total_ports||24} · 📍 ${dev.location||'—'}</small>", 'список устройств: адрес')

rep("<button class=\"btn btn-primary\" style=\"padding:.3rem .8rem;\" onclick=\"focusDevice(${d.id})\">🎯 Показать</button>",
"""<button class="btn btn-primary" style="padding:.3rem .8rem;" onclick="focusDevice(${d.id})">🎯 Показать</button>
            <button class="btn btn-secondary" style="padding:.3rem .8rem;" onclick="setLoc(${d.id})">📍</button>""", 'кнопка правки адреса')

rep("function focusDevice(id){",
"""function setLoc(id){
  var dev=devices.find(function(d){return d.id===id;});
  var v=prompt('Адрес коммутатора:', dev? (dev.location||'') : '');
  if(v===null) return;
  fetch('/api/network-map/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:v})}).then(function(){loadMap();});
}
function focusDevice(id){""", 'JS setLoc')

rep('<div class="form-group"><label>Наряд №:</label><input id="stOrder"></div>',
'''<div class="form-group"><label>Наряд №:</label><input id="stOrder"></div>
<div class="form-group"><label>Адрес:</label><input id="stLoc" placeholder="Где стоит"></div>''', 'склад: поле адреса')

rep('<thead><tr><th>Модель</th><th>Серийник</th><th>Последний IP</th><th>Наряд</th>',
    '<thead><tr><th>Модель</th><th>Серийник</th><th>Последний IP</th><th>Адрес</th><th>Наряд</th>', 'склад: шапка')

rep("<td>${r.last_ip||'-'}</td><td>${r.order_number||'-'}</td>",
    "<td>${r.last_ip||'-'}</td><td>${r.location||'-'}</td><td>${r.order_number||'-'}</td>", 'склад: строка')

rep("order_number:document.getElementById('stOrder').value,",
"""order_number:document.getElementById('stOrder').value,
        location:document.getElementById('stLoc').value,""", 'склад: save location')

rep("INSERT INTO switch_inventory (model, serial, last_ip, status, order_number, notes, updated_at) VALUES (?,?,?,?,?,?,?)",
    "INSERT INTO switch_inventory (model, serial, last_ip, location, status, order_number, notes, updated_at) VALUES (?,?,?,?,?,?,?,?)", 'склад: insert columns')

rep("(d.get('model',''), d.get('serial',''), d.get('last_ip',''),",
    "(d.get('model',''), d.get('serial',''), d.get('last_ip',''), d.get('location',''),", 'склад: insert params')

rep("for f in ('model','serial','last_ip','status','order_number','notes'):",
    "for f in ('model','serial','last_ip','status','order_number','notes','location'):", 'склад: PUT location')

rep("L.append('Адрес: %s' % (o['old_switch_location'] or ''))",
"""L.append('Адрес: %s' % (o['old_switch_location'] or ''))
    L.append('Тип наряда: %s' % ('новая установка' if o['order_type'] == 'new' else 'сервис' if o['order_type'] == 'service' else 'замена'))
    L.append('Адрес нового: %s' % (o['new_switch_location'] or '—'))""", 'отчёт: тип+адрес')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')