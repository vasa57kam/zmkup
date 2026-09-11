import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Убрать дубли ссылки «Полевой» и добавить защиту
FIELD_LINK = '<a href="/field" class="nav-link">📱 Полевой</a>'
cnt = src.count(FIELD_LINK)
if cnt > 1:
    src = src.replace(FIELD_LINK, '')
    print('  ok: дубли Полевой удалены (' + str(cnt) + ')')
if FIELD_LINK not in src:
    rep('<a href="/commands" class="nav-link">📚 Команды</a>',
        '<a href="/commands" class="nav-link">📚 Команды</a>\n            ' + FIELD_LINK,
        'ссылка Полевой (одна)')

# 2) Паспорт в отдельный модуль — авто-патчи его больше не съедят
PASS_MOD = '''PASS_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Паспорт наряда {{ o.order_number }}</title>
<style>
body{font-family:Arial,sans-serif;font-size:12px;color:#000;margin:15mm 15mm;}
h1{font-size:18px;margin:0 0 6px;} h2{font-size:14px;margin:14px 0 6px;}
table{width:100%;border-collapse:collapse;margin:6px 0;}
td,th{border:1px solid #000;padding:4px 6px;font-size:11px;text-align:left;vertical-align:top;}
.noprint{margin:0 0 12px;} @media print{.noprint{display:none;}}
</style></head><body>
<div class="noprint"><button onclick="window.print()" style="padding:8px 16px;font-size:14px;cursor:pointer;">🖨️ Печать</button> <a href="/order/{{ o.id }}">← К наряду</a></div>
<h1>ПАСПОРТ НАРЯДА № {{ o.order_number }}</h1>
<p>Дата: {{ o.created_at }} | Тип: {{ o.order_type or 'replace' }} | Статус: {{ o.status }}</p>
<h2>1. Оборудование</h2>
<table><tr><th></th><th>IP</th><th>Модель</th><th>Портов</th><th>Адрес</th></tr>
<tr><td>Старый</td><td>{{ o.old_switch_ip or '—' }}</td><td>{{ o.old_switch_model or '—' }}</td><td>{{ o.old_switch_ports }}</td><td>{{ o.old_switch_location or '—' }}</td></tr>
<tr><td>Новый</td><td>{{ o.new_switch_ip or '—' }}</td><td>{{ o.new_switch_model or '—' }}</td><td>{{ o.new_switch_ports }}</td><td>{{ o.new_switch_location or '—' }}</td></tr></table>
<h2>2. Подключения</h2>
<table><tr><th>Тип</th><th>Порт (стар)</th><th>Порт (нов)</th><th>Устройство</th><th>Порт там</th></tr>
{% for l in links %}<tr><td>{{ l.link_type }}</td><td>{{ l.old_port }}</td><td>{{ l.new_port or '—' }}</td><td>{{ l.upstream_device }}</td><td>{{ l.upstream_port }}</td></tr>{% endfor %}</table>
<h2>3. Камеры</h2>
{% if cams %}<table><tr><th></th><th>Модель</th><th>Серийник</th><th>IP/ID</th><th>Логин</th><th>Свитч:порт</th><th>RTSP</th><th>Зона</th></tr>
{% for c in cams %}<tr><td>{{ 'СТАР' if c.side=='old' else 'НОВ' }}</td><td>{{ c.model or '—' }}</td><td>{{ c.serial or '—' }}</td><td>{{ c.ip or '—' }}</td><td>{{ c.login or '—' }}</td><td>{{ (c.switch_name or '—') ~ ':' ~ (c.switch_port or '—') }}</td><td>{{ c.rtsp or '—' }}</td><td>{{ c.zone or '—' }}</td></tr>{% endfor %}</table>
{% else %}<p>Камер нет.</p>{% endif %}
<h2>4. Абоненты ({{ subs|length }})</h2>
{% if subs %}<table><tr><th>Порт (стар)</th><th>Порт (нов)</th><th>Абонент</th><th>Адрес</th><th>VLAN</th><th>MAC</th></tr>
{% for s in subs %}<tr><td>{{ s.old_port }}</td><td>{{ s.new_port or '—' }}</td><td>{{ s.subscriber_name or '' }}</td><td>{{ s.address or '' }}</td><td>{{ s.vlan or '' }}</td><td>{{ s.mac_address or '' }}</td></tr>{% endfor %}</table>
{% else %}<p>Абонентов нет.</p>{% endif %}
<h2>5. Контроль FDB</h2>
<p>Записей ДО: {{ oldn }} | ПОСЛЕ: {{ newn }} | Потеряно MAC: {{ lost|length }}</p>
<h2>6. Чек-лист работ</h2>
<table>{% for s in steps %}<tr><td style="width:10px;text-align:center;">{{ '☑' if (s.done or fl.get(loop.index0)) else '☐' }}</td><td>{{ s.step_text }}</td></tr>{% endfor %}</table>
<h2>Подписи</h2>
<table><tr><td style="height:60px;">Работу выполнил: ____________________</td><td style="height:60px;">Принял: ____________________</td></tr></table>
</body></html>"""


def register(app, get_db, auto_flags):
    from flask import render_template_string, jsonify

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
        try:
            cams = conn.execute('SELECT * FROM cameras WHERE order_id=? ORDER BY side', (order_id,)).fetchall()
        except Exception:
            cams = []
        oldf = conn.execute("SELECT * FROM fdb_tables WHERE order_id=? AND switch_type='old'", (order_id,)).fetchall()
        newf = conn.execute("SELECT * FROM fdb_tables WHERE order_id=? AND switch_type='new'", (order_id,)).fetchall()
        conn.close()
        fl = auto_flags(order_id)
        om = {r['mac_address'].upper(): r for r in oldf if r['mac_address']}
        nm = {r['mac_address'].upper(): r for r in newf if r['mac_address']}
        lost = [(m, om[m]['port'], om[m]['subscriber'] or '') for m in sorted(set(om) - set(nm))]
        return render_template_string(PASS_HTML, o=o, links=links, subs=subs, cams=cams,
            steps=steps, fl=fl, oldn=len(oldf), newn=len(newf), lost=lost)
'''
open('passport_mod.py', 'w').write(PASS_MOD)
print('ok: passport_mod.py записан')

# вырезать старый паспорт из swh.py, если он там ещё есть
i = src.find('PASS_HTML = """')
if i >= 0 and 'def passport(order_id):' in src[i:i+8000]:
    d = src.find('def passport(', i)
    ends = [x for x in (src.find('\n@app.route', d), src.find('\ndef ', d), src.find('\nPASS_HTML', d + 10)) if x > 0]
    j = min(ends) if ends else -1
    if j > 0:
        src = src[:i] + src[j+1:]
        print('ok: старый паспорт вырезан из swh.py')

if 'import passport_mod' not in src:
    rep('from flask_cors import CORS', 'from flask_cors import CORS\nimport passport_mod', 'импорт passport_mod')
if 'passport_mod.register' not in src:
    rep("if __name__ == '__main__':",
        "passport_mod.register(app, get_db, auto_flags)\n\nif __name__ == '__main__':",
        'регистрация паспорта')

# 3) Сторож: следить и за модулем паспорта
rep("'def passport(order_id):', 'def admin_job', 'def cameras_api', 'def commands_page'",
    "'passport_mod.register(', 'def admin_job', 'def cameras_api', 'def commands_page'",
    'сторож: маркер модуля')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')