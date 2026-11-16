# update.py v28: настоящие права гостя — админ решает что можно, DELETE и /admin/* закрыты навсегда
import ast, json, os, re, shutil, sqlite3
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v28_' + TS + '.py')

src = open('swh.py', encoding='utf-8').read()
FIXES = []

# --- 1. Таблица прав гостя в init_db ---
if 'CREATE TABLE IF NOT EXISTS guest_permissions' not in src:
    rep_src = src
    # ищем executescript и добавляем таблицу в него
    if "CREATE TABLE IF NOT EXISTS update_log" in src:
        src = src.replace(
            "CREATE TABLE IF NOT EXISTS update_log (\n        id INTEGER PRIMARY KEY AUTOINCREMENT,\n        ts TEXT, source TEXT, rc INTEGER, out TEXT, code TEXT\n    );",
            """CREATE TABLE IF NOT EXISTS update_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, source TEXT, rc INTEGER, out TEXT, code TEXT
    );
    CREATE TABLE IF NOT EXISTS guest_permissions (
        key TEXT PRIMARY KEY,
        val INTEGER DEFAULT 0
    );""", 1)
        FIXES.append('table guest_permissions'); print('  ok: таблица guest_permissions')

# --- 2. Дефолтные права (записываются только при первом запуске) ---
GP_DEFAULTS = {
    'can_view_orders': 1,
    'can_create_orders': 0,
    'can_edit_orders': 0,
    'can_view_map': 1,
    'can_edit_map': 0,
    'can_view_vlans': 1,
    'can_view_kb': 1,
    'can_view_gen': 1,
    'can_view_tools': 1,
    'can_view_inventory': 1,
    'can_edit_inventory': 0,
    'can_view_schemes': 1,
    'can_edit_schemes': 0,
    'can_view_stock': 1,
    'can_view_field': 1,
    'can_view_netlab': 1,
    'can_edit_attachments': 0,
    'can_edit_notes': 0,
    'can_edit_fdb': 0,
}
if 'GP_DEFAULTS' not in src:
    block = '''
# --- ПРАВА ГОСТЯ (управляются админом) ---
GP_DEFAULTS = ''' + repr(GP_DEFAULTS) + '''

def _gp(key, default=None):
    if default is None:
        default = GP_DEFAULTS.get(key, 0)
    try:
        conn = sqlite3.connect('switch_replacements.db')
        r = conn.execute("SELECT val FROM guest_permissions WHERE key=?", (key,)).fetchone()
        if r is None:
            conn.execute("INSERT INTO guest_permissions (key,val) VALUES (?,?)", (key, int(default)))
            conn.commit(); conn.close()
            return int(default)
        conn.close()
        return int(r[0])
    except Exception:
        return int(default)

def _gp_set(key, val):
    try:
        conn = sqlite3.connect('switch_replacements.db')
        conn.execute("INSERT OR REPLACE INTO guest_permissions (key,val) VALUES (?,?)", (key, int(bool(val))))
        conn.commit(); conn.close()
    except Exception:
        pass

@app.route('/api/admin/guest_perms', methods=['GET', 'POST'])
def admin_guest_perms():
    if session.get('role') != 'admin':
        return jsonify({'error': 'admin only'}), 403
    if request.method == 'GET':
        out = {}
        for k in GP_DEFAULTS:
            out[k] = _gp(k)
        return jsonify(out)
    d = request.json or {}
    key = d.get('key')
    if key not in GP_DEFAULTS:
        return jsonify({'error': 'unknown key'}), 400
    _gp_set(key, d.get('val'))
    return jsonify({'ok': True, 'key': key, 'val': _gp(key)})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + block + src[idx:]
    FIXES.append('GP defaults + endpoints'); print('  ok: права гостя + эндпоинты')

# --- 3. ПОЛНАЯ ЗАМЕНА _global_auth на серверный whitelist ---
old_auth = re.search(r"@app\.before_request\s*\ndef _global_auth\(\):.*?(?=\n@app\.|\nif __name__)", src, re.S)
if old_auth:
    new_auth = '''@app.before_request
def _global_auth():
    # публичные маршрусы — без проверки
    if any(request.path.startswith(p) for p in PUBLIC_PREFIXES):
        return None
    # не авторизован — на /login
    if 'role' not in session:
        if request.path.startswith('/api/'):
            return jsonify({'error': 'not logged in'}), 401
        if request.path != '/login':
            return redirect('/login?next=' + request.path)
    role = session.get('role')
    # админу — всё
    if role == 'admin':
        return None
    # === ГОСТЬ: строгий whitelist ===
    m = request.method
    p = request.path
    # ХАРДКОД: DELETE гостю запрещён ВСЕГДА, независимо от галочек
    if m == 'DELETE':
        return jsonify({'error': 'guest: delete forbidden'}), 403
    # ХАРДКОД: админские эндпоинты гостю запрещены ВСЕГДА (кроме чтения guest_perms)
    if p.startswith('/api/admin/'):
        return jsonify({'error': 'admin only'}), 403
    # PUT гостю запрещён, кроме исключений ниже
    if m == 'PUT':
        if p.startswith('/api/orders/') and _gp('can_edit_orders'):
            return None
        return jsonify({'error': 'guest: edit forbidden'}), 403
    # POST — только явно разрешённые
    if m == 'POST':
        # выход / логин / whoami — всегда
        if p.startswith('/api/auth/'):
            return None
        # создание наряда
        if (p.startswith('/api/orders-upsert') or p.startswith('/api/orders/')) and not _gp('can_create_orders'):
            return jsonify({'error': 'guest: создание нарядов запрещено'}), 403
        # карта
        if (p.startswith('/api/network-map') or p.startswith('/api/map-connections')) and not _gp('can_edit_map'):
            return jsonify({'error': 'guest: карта только просмотр'}), 403
        # инвентарь
        if p.startswith('/api/inventory') and not _gp('can_edit_inventory'):
            return jsonify({'error': 'guest: инвентарь только просмотр'}), 403
        # вложения
        if p.startswith('/api/attachments') and not _gp('can_edit_attachments'):
            return jsonify({'error': 'guest: вложения только просмотр'}), 403
        # заметки
        if p.startswith('/api/notes/') and not _gp('can_edit_notes'):
            return jsonify({'error': 'guest: заметки только просмотр'}), 403
        # FDB
        if (p.startswith('/api/fdb') or p.startswith('/api/fdb-paste')) and not _gp('can_edit_fdb'):
            return jsonify({'error': 'guest: FDB только просмотр'}), 403
        # схемы
        if p.startswith('/api/schemes') and not _gp('can_edit_schemes'):
            return jsonify({'error': 'guest: схемы только просмотр'}), 403
        # отчёты/генерация команд — разрешено
        if p.startswith('/api/report') or p.startswith('/api/tools/'):
            return None
    # GET: страницы по правам просмотра
    if m == 'GET':
        if p == '/map' and not _gp('can_view_map'):
            return redirect('/?denied=map')
        if p.startswith('/order/') and not _gp('can_view_orders'):
            return redirect('/?denied=orders')
        if p == '/vlans' and not _gp('can_view_vlans'):
            return redirect('/?denied=vlans')
        if p == '/kb' and not _gp('can_view_kb'):
            return redirect('/?denied=kb')
        if p == '/gen' and not _gp('can_view_gen'):
            return redirect('/?denied=gen')
        if p == '/tools' and not _gp('can_view_tools'):
            return redirect('/?denied=tools')
        if p == '/stock' and not _gp('can_view_stock'):
            return redirect('/?denied=stock')
        if p == '/field' and not _gp('can_view_field'):
            return redirect('/?denied=field')
        if p == '/netlab' and not _gp('can_view_netlab'):
            return redirect('/?denied=netlab')
        return None
    return jsonify({'error': 'guest: method not allowed'}), 405
'''
    src = src[:old_auth.start()] + new_auth + src[old_auth.end():]
    FIXES.append('server guard whitelist'); print('  ok: server guard переписан (whitelist + DELETE=forbidden + /admin/*=forbidden)')

# --- 4. Блок UI прав гостя в /admin ---
if 'id="guestPermsBlock"' not in src:
    ui_block = '''<div class="card" id="guestPermsBlock" style="background:#fff;padding:1rem;border-radius:8px;margin:1rem 0;">
<h3>👁 Права гостевого доступа</h3>
<p style="color:#7f8c8d;margin-top:0;">Гость входит по гостевому паролю. Отметьте, что ему можно.<br>
<b style="color:#c0392b;">Удаление (DELETE) и админские действия запрещены гостю навсегда</b> — даже если случайно включить галочку, сервер вернёт 403.</p>
<div style="columns:2;gap:20px;font-size:14px;" id="gpList">
  <label><input type="checkbox" data-gp="can_view_orders"> смотреть наряды</label><br>
  <label><input type="checkbox" data-gp="can_create_orders"> создавать наряды</label><br>
  <label><input type="checkbox" data-gp="can_edit_orders"> редактировать наряды</label><br>
  <label><input type="checkbox" data-gp="can_view_map"> смотреть карту сети</label><br>
  <label><input type="checkbox" data-gp="can_edit_map"> редактировать карту</label><br>
  <label><input type="checkbox" data-gp="can_view_vlans"> VLAN-справочник</label><br>
  <label><input type="checkbox" data-gp="can_view_kb"> база знаний</label><br>
  <label><input type="checkbox" data-gp="can_view_gen"> генератор команд</label><br>
  <label><input type="checkbox" data-gp="can_view_tools"> инструмент SSH/TELNET</label><br>
  <label><input type="checkbox" data-gp="can_view_inventory"> склад / инвентарь</label><br>
  <label><input type="checkbox" data-gp="can_edit_inventory"> редактировать инвентарь</label><br>
  <label><input type="checkbox" data-gp="can_view_schemes"> схемы ЛВС</label><br>
  <label><input type="checkbox" data-gp="can_edit_schemes"> редактировать/удалять схемы</label><br>
  <label><input type="checkbox" data-gp="can_view_stock"> резерв/склад</label><br>
  <label><input type="checkbox" data-gp="can_view_field"> полевые заметки</label><br>
  <label><input type="checkbox" data-gp="can_view_netlab"> NetLab (симуляция)</label><br>
</div>
<div id="gpMsg" style="margin-top:8px;color:#27ae60;font-size:13px;"></div>
</div>
'''
    rep('<h3>🔄 Автозапуск после ребута и обновлений</h3>',
        ui_block + '<h3>🔄 Автозапуск после ребута и обновлений</h3>',
        'блок прав гостя в /admin')

# --- 5. JS: загрузка и сохранение прав + inject роли в body ---
ajs_path = 'static/admin.js'
if os.path.exists(ajs_path):
    ajs = open(ajs_path, encoding='utf-8').read()
    if 'function loadGuestPerms()' not in ajs:
        ajs += '''
function loadGuestPerms(){
  var list=document.getElementById('gpList'); if(!list) return;
  fetch('/api/admin/guest_perms').then(function(r){return r.json();}).then(function(perms){
    Array.prototype.forEach.call(list.querySelectorAll('[data-gp]'), function(cb){
      cb.checked = !!perms[cb.dataset.gp];
      cb.onchange = function(){
        fetch('/api/admin/guest_perms',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({key:cb.dataset.gp, val:cb.checked?1:0})})
        .then(function(r){return r.json();}).then(function(res){
          var m=document.getElementById('gpMsg');
          if(m){ m.textContent = res.ok? '✓ сохранено: '+cb.dataset.gp+' = '+(cb.checked?'ДА':'НЕТ') : ('ошибка: '+(res.error||'')); setTimeout(function(){m.textContent='';},2000); }
        });
      };
    });
  });
}
'''
        ajs = ajs.replace('  loadAutostart();', '  loadAutostart();\n  loadGuestPerms();', 1)
        open(ajs_path, 'w', encoding='utf-8').write(ajs)
        FIXES.append('admin.js gp loader'); print('  ok: admin.js loadGuestPerms')

# --- 6. Инъекция класса role-* в <body> + CSS скрытия опасных кнопок для гостя ---
if 'role-guest-css' not in src:
    ep = '''
@app.after_request
def _inject_role(resp):
    try:
        if 'text/html' not in (resp.content_type or ''):
            return resp
        t = resp.get_data(as_text=True)
        if 'data-role-injected' in t:
            return resp
        role = session.get('role', '')
        cls = 'role-admin' if role == 'admin' else ('role-guest' if role == 'guest' else 'role-anon')
        css = """<style id="role-guest-css">
body.role-guest .btn-danger,
body.role-guest [onclick*="elete"],
body.role-guest [onclick*="eleteOrder"],
body.role-guest [onclick*="eleteScheme"],
body.role-guest [onclick*="eleteDevice"],
body.role-guest [data-admin-only],
body.role-guest a[href="/admin"]{ display:none !important; }
body.role-guest .admin-badge::after{ content:" · 👁 только просмотр"; color:#c0392b; font-size:11px; }
</style>"""
        # добавим класс к body
        import re as _re
        t = _re.sub(r'<body([^>]*)>', '<body\\1 class="'+cls+'" data-role-injected="1">', t, count=1)
        t = t.replace('</head>', css + '</head>', 1)
        resp.set_data(t)
    except Exception:
        pass
    return resp


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    FIXES.append('inject role class + hide UI'); print('  ok: inject role-* + скрытие кнопок удаления у гостя')

# --- 7. Проверка + запись ---
try:
    ast.parse(src)
    print('  ok: ast.parse swh.py')
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v28_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))

open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v28', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v28. Правок:', len(FIXES), '| бэкап: backups/swh_pre_v28_' + TS + '.py')
