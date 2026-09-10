import ast
src = open('swh.py').read()
def rep(old, new, label, all_=False):
    global src
    if old in src:
        src = src.replace(old, new) if all_ else src.replace(old, new, 1)
        print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Возврат маршрута паспорта, если его снова снесли
if 'def passport(order_id):' not in src:
    PASS = '''PASS_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Паспорт наряда {{ o.order_number }}</title>
<style>
body{font-family:Arial,sans-serif;font-size:12px;color:#000;margin:15mm 15mm;}
h1{font-size:18px;margin:0 0 6px;} h2{font-size:14px;margin:14px 0 6px;}
table{width:100%;border-collapse:collapse;margin:6px 0;}
td,th{border:1px solid #000;padding:4px 6px;font-size:11px;text-align:left;vertical-align:top;}
.noprint{margin:0 0 12px;} @media print{.noprint{display:none;}}
</style></head><body>
<div class="noprint">
<button onclick="window.print()" style="padding:8px 16px;font-size:14px;cursor:pointer;">🖨️ Печать</button>
<a href="/order/{{ o.id }}">← К наряду</a>
</div>
<h1>ПАСПОРТ НАРЯДА № {{ o.order_number }}</h1>
<p>Дата: {{ o.created_at }} | Тип: {{ 'новая установка' if o.order_type=='new' else 'сервис' if o.order_type=='service' else 'камера' if o.order_type=='camera' else 'замена коммутатора' }} | Статус: {{ o.status }}</p>
<h2>1. Оборудование</h2>
<table>
<tr><th></th><th>IP</th><th>Модель</th><th>Портов</th><th>Адрес</th></tr>
<tr><td>Старый</td><td>{{ o.old_switch_ip or '—' }}</td><td>{{ o.old_switch_model or '—' }}</td><td>{{ o.old_switch_ports }}</td><td>{{ o.old_switch_location or '—' }}</td></tr>
<tr><td>Новый</td><td>{{ o.new_switch_ip or '—' }}</td><td>{{ o.new_switch_model or '—' }}</td><td>{{ o.new_switch_ports }}</td><td>{{ o.new_switch_location or '—' }}</td></tr>
</table>
<h2>2. Подключения</h2>
<table><tr><th>Тип</th><th>Порт (стар)</th><th>Порт (нов)</th><th>Устройство</th><th>Адрес устройства</th><th>Порт там</th></tr>
{% for l in links %}<tr><td>{{ 'UPLINK' if l.link_type=='uplink' else 'downlink' }}</td><td>{{ l.old_port }}</td><td>{{ l.new_port or '—' }}</td><td>{{ l.upstream_device }}</td><td>{{ dev_loc(l.upstream_device) or '—' }}</td><td>{{ l.upstream_port }}</td></tr>{% endfor %}
</table>
<h2>3. Камеры</h2>
{% if cams %}<table><tr><th></th><th>Модель</th><th>Серийник</th><th>IP/ID</th><th>MAC</th><th>Зона</th></tr>
{% for c in cams %}<tr><td>{{ 'СТАР' if c.side=='old' else 'НОВ' }}</td><td>{{ c.model or '—' }}</td><td>{{ c.serial or '—' }}</td><td>{{ c.ip or '—' }}</td><td>{{ c.mac or '—' }}</td><td>{{ c.zone or '—' }}</td></tr>{% endfor %}
</table>{% else %}<p>Камер нет.</p>{% endif %}
<h2>4. Абоненты ({{ subs|length }})</h2>
{% if subs %}<table><tr><th>Порт (стар)</th><th>Порт (нов)</th><th>Абонент</th><th>Адрес</th><th>VLAN</th><th>MAC</th></tr>
{% for s in subs %}<tr><td>{{ s.old_port }}</td><td>{{ s.new_port or '—' }}</td><td>{{ s.subscriber_name or '' }}</td><td>{{ s.address or '' }}</td><td>{{ s.vlan or '' }}</td><td>{{ s.mac_address or '' }}</td></tr>{% endfor %}
</table>{% else %}<p>Абонентов нет.</p>{% endif %}
<h2>5. Контроль FDB</h2>
<p>Записей ДО: {{ oldn }} | ПОСЛЕ: {{ newn }} | Потеряно MAC: {{ lost|length }}</p>
{% if lost %}<table><tr><th>MAC</th><th>Порт</th><th>Абонент</th></tr>{% for m in lost %}<tr><td>{{ m[0] }}</td><td>{{ m[1] }}</td><td>{{ m[2] }}</td></tr>{% endfor %}</table>{% endif %}
<h2>6. Чек-лист работ</h2>
<table>{% for s in steps %}<tr><td style="width:10px;text-align:center;">{{ '☑' if (s.done or fl.get(loop.index0)) else '☐' }}</td><td>{{ s.step_text }}</td></tr>{% endfor %}</table>
{% if o.commands_used %}<h2>7. Использованные команды</h2><p>{{ o.commands_used }}</p><p>Нужна была машина: {{ 'ДА' if o.vehicle_needed else 'нет' }}</p>{% endif %}
<h2>Подписи</h2>
<table><tr><td style="height:60px;">Работу выполнил: ____________________</td><td style="height:60px;">Принял: ____________________</td></tr></table>
</body></html>"""

@app.route('/passport/<int:order_id>')
def passport(order_id):
    conn = get_db()
    o = conn.execute('SELECT * FROM work_orders WHERE id=?', (order_id,)).fetchone()
    if not o:
        conn.close()
        return 'Наряд не найден', 404
    links = conn.execute('SELECT * FROM links WHERE order_id=? ORDER BY link_type, old_port', (order_id,)).fetchall()
    subs = conn.execute('SELECT * FROM subscribers WHERE order_id=? ORDER BY old_port', (order_id,)).fetchall()
    steps = conn.execute('SELECT * FROM order_steps WHERE order_id=? ORDER BY pos', (order_id,)).fetchall()
    cams = conn.execute('SELECT * FROM cameras WHERE order_id=? ORDER BY side', (order_id,)).fetchall()
    oldf = conn.execute("SELECT * FROM fdb_tables WHERE order_id=? AND switch_type='old'", (order_id,)).fetchall()
    newf = conn.execute("SELECT * FROM fdb_tables WHERE order_id=? AND switch_type='new'", (order_id,)).fetchall()
    conn.close()
    fl = auto_flags(order_id)
    om = {r['mac_address'].upper(): r for r in oldf if r['mac_address']}
    nm = {r['mac_address'].upper(): r for r in newf if r['mac_address']}
    lost = [(m, om[m]['port'], om[m]['subscriber'] or '') for m in sorted(set(om) - set(nm))]
    return render_template_string(PASS_HTML, o=o, links=links, subs=subs, cams=cams,
        steps=steps, fl=fl, oldn=len(oldf), newn=len(newf), lost=lost, dev_loc=dev_loc)


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + PASS + src[idx:]
    print('ok: паспорт возвращён (+камеры в паспорте)')
else:
    print('паспорт на месте')

# 2) Песочница: дымовые тесты теперь включают паспорт/наряд/планировщик
rep("""urls = ['/', '/map', '/commands', '/admin', '/api/orders', '/api/inventory', '/api/network-map', '/api/commands']""",
"""import sqlite3 as _sq
_oid = 1
try:
    _c = _sq.connect('switch_replacements.db')
    _r = _c.execute('SELECT id FROM work_orders ORDER BY id LIMIT 1').fetchone()
    _c.close()
    if _r:
        _oid = _r[0]
except Exception:
    pass
urls = ['/', '/map', '/commands', '/admin', '/api/orders', '/api/inventory', '/api/network-map', '/api/commands',
        '/passport/%d' % _oid, '/order/%d' % _oid, '/planner/%d' % _oid]""", 'дымовые тесты: паспорт/наряд/планировщик')

# 3) Файлы (конфиги/бэкапы) к камерам
import os
ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'camFiles_' not in ajs:
    ajs = ajs.replace("""   +'<button class="btn btn-secondary" onclick="importCam('+c.id+')">📥 Импорт конфига</button>'
   +'</div>';""",
"""   +'<button class="btn btn-secondary" onclick="importCam('+c.id+')">📥 Импорт конфига</button>'
   +'<div class="form-group" style="margin-top:.5rem;"><label>Файлы камеры (конфиг, бэкап, фото шильдика):</label>'
   +'<div id="camFiles_'+c.id+'"></div>'
   +'<input type="file" onchange="uploadAttachment(\\'camera\\','+c.id+',\\'camFiles_'+c.id+'\\',this)"></div>'
   +'</div>';""", 1)
    ajs = ajs.replace("""    box.innerHTML=rows.map(camCard).join('')||'<small>Камер в наряде пока нет.</small>';""",
"""    box.innerHTML=rows.map(camCard).join('')||'<small>Камер в наряде пока нет.</small>';
    rows.forEach(function(r){ loadAttachments('camera', r.id, 'camFiles_'+r.id); });""", 1)
    open(ajs_path, 'w').write(ajs)
    print('ok: файлы к камерам')
else:
    print('файлы камер уже есть')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')