import ast, json, os, re, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v29_' + TS + '.py')
src = open('swh.py', encoding='utf-8').read()
FIXES = []

# === 1. Таблица guest_permissions ===
if 'guest_permissions' not in src:
    try:
        import sqlite3
        c = sqlite3.connect('switch_replacements.db')
        c.execute('CREATE TABLE IF NOT EXISTS guest_permissions (key TEXT PRIMARY KEY, val INTEGER DEFAULT 0)')
        c.commit(); c.close()
        FIXES.append('table guest_permissions in DB')
    except Exception as e:
        print('DB table err:', e)

# === 2. Константа GP_DEFAULTS + функции _gp ===
if 'GP_DEFAULTS_V29' not in src:
    block = '''
# --- GP_DEFAULTS_V29 (права гостя) ---
GP_DEFAULTS_V29 = {
    'can_view_orders':1,'can_create_orders':0,'can_edit_orders':0,
    'can_view_map':1,'can_edit_map':0,
    'can_view_vlans':1,'can_view_kb':1,'can_view_gen':1,'can_view_tools':1,
    'can_view_inventory':1,'can_edit_inventory':0,
    'can_view_schemes':1,'can_edit_schemes':0,
    'can_view_stock':1,'can_view_field':1,'can_view_netlab':1,
    'can_edit_attachments':0,'can_edit_notes':0,'can_edit_fdb':0,
}
def _gp_v29(key, default=None):
    if default is None: default = GP_DEFAULTS_V29.get(key, 0)
    try:
        import sqlite3 as _s3
        c = _s3.connect('switch_replacements.db')
        r = c.execute("SELECT val FROM guest_permissions WHERE key=?", (key,)).fetchone()
        if r is None:
            c.execute("INSERT INTO guest_permissions (key,val) VALUES (?,?)", (key, int(default)))
            c.commit(); c.close(); return int(default)
        c.close(); return int(r[0])
    except Exception: return int(default)

def _gp_set_v29(key, val):
    try:
        import sqlite3 as _s3
        c = _s3.connect('switch_replacements.db')
        c.execute("INSERT OR REPLACE INTO guest_permissions (key,val) VALUES (?,?)", (key, int(bool(val))))
        c.commit(); c.close()
    except Exception: pass

@app.route('/api/admin/guest_perms', methods=['GET','POST'])
def admin_guest_perms_v29():
    if session.get('role') != 'admin':
        return jsonify({'error':'admin only'}), 403
    if request.method == 'GET':
        out = {k: _gp_v29(k) for k in GP_DEFAULTS_V29}
        return jsonify(out)
    d = request.json or {}
    k = d.get('key')
    if k not in GP_DEFAULTS_V29: return jsonify({'error':'unknown'}), 400
    _gp_set_v29(k, d.get('val'))
    return jsonify({'ok':True, 'key':k, 'val':_gp_v29(k)})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + block + src[idx:]
    FIXES.append('GP_DEFAULTS_V29 + endpoints')
    print('  ok: GP_DEFAULTS_V29 + /api/admin/guest_perms')

# === 3. UI-блок прав в /admin ===
if 'id="guestPermsBlock"' not in src:
    ui = '''<div class="card" id="guestPermsBlock" style="background:#fff;padding:1rem;border-radius:8px;margin:1rem 0;">
<h3>👁 Права гостевого доступа</h3>
<p style="color:#7f8c8d;margin-top:0;">Отметьте, что можно гостю.<br>
<b style="color:#c0392b;">DELETE и /admin/* запрещены гостю навсегда</b> (на уровне сервера).</p>
<div style="columns:2;gap:20px;font-size:14px;" id="gpList">
<label><input type="checkbox" data-gp="can_view_orders"> смотреть наряды</label><br>
<label><input type="checkbox" data-gp="can_create_orders"> создавать наряды</label><br>
<label><input type="checkbox" data-gp="can_edit_orders"> редактировать наряды</label><br>
<label><input type="checkbox" data-gp="can_view_map"> смотреть карту</label><br>
<label><input type="checkbox" data-gp="can_edit_map"> редактировать карту</label><br>
<label><input type="checkbox" data-gp="can_view_vlans"> VLAN-справочник</label><br>
<label><input type="checkbox" data-gp="can_view_kb"> база знаний</label><br>
<label><input type="checkbox" data-gp="can_view_gen"> генератор команд</label><br>
<label><input type="checkbox" data-gp="can_view_tools"> SSH/TELNET</label><br>
<label><input type="checkbox" data-gp="can_view_inventory"> склад</label><br>
<label><input type="checkbox" data-gp="can_edit_inventory"> редактировать склад</label><br>
<label><input type="checkbox" data-gp="can_view_schemes"> схемы ЛВС</label><br>
<label><input type="checkbox" data-gp="can_edit_schemes"> редактировать схемы</label><br>
<label><input type="checkbox" data-gp="can_view_stock"> резерв</label><br>
<label><input type="checkbox" data-gp="can_view_field"> полевые заметки</label><br>
<label><input type="checkbox" data-gp="can_view_netlab"> NetLab</label><br>
</div>
<div id="gpMsg" style="margin-top:8px;color:#27ae60;font-size:13px;"></div>
</div>
'''
    if '<h3>🔄 Автозапуск после ребута и обновлений</h3>' in src:
        src = src.replace('<h3>🔄 Автозапуск после ребута и обновлений</h3>',
                          ui + '<h3>🔄 Автозапуск после ребута и обновлений</h3>', 1)
        FIXES.append('UI блок guestPermsBlock'); print('  ok: UI блок')
    else:
        # fallback: перед закрывающим div админки
        idx = src.rfind('</div>\n</div>\n</body>')
        if idx > 0:
            src = src[:idx] + ui + src[idx:]
            FIXES.append('UI блок (fallback)'); print('  ok: UI блок (fallback)')

# === 4. JS для смены прав (в admin.js или inject) ===
ajs_path = 'static/admin.js'
if os.path.exists(ajs_path):
    ajs = open(ajs_path, encoding='utf-8').read()
    if 'loadGuestPerms_v29' not in ajs:
        ajs += '''
function loadGuestPerms_v29(){
  var list=document.getElementById('gpList'); if(!list) return;
  fetch('/api/admin/guest_perms').then(function(r){return r.json();}).then(function(perms){
    Array.prototype.forEach.call(list.querySelectorAll('[data-gp]'), function(cb){
      cb.checked = !!perms[cb.dataset.gp];
      cb.onchange = function(){
        fetch('/api/admin/guest_perms',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({key:cb.dataset.gp, val:cb.checked?1:0})})
        .then(function(r){return r.json();}).then(function(res){
          var m=document.getElementById('gpMsg');
          if(m){ m.textContent = res.ok? '✓ '+(cb.checked?'включено':'выключено')+': '+cb.dataset.gp : ('ошибка: '+(res.error||'')); setTimeout(function(){m.textContent='';},2000); }
        });
      };
    });
  });
}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',loadGuestPerms_v29);}else{loadGuestPerms_v29();}
'''
        open(ajs_path, 'w', encoding='utf-8').write(ajs)
        FIXES.append('admin.js gp loader'); print('  ok: admin.js gp loader')

# === 5. Inject роли в body + CSS для скрытия опасных кнопок у гостя ===
if 'role-guest-css-v29' not in src:
    ep = '''
@app.after_request
def _inject_role_v29(resp):
    try:
        if 'text/html' not in (resp.content_type or ''): return resp
        t = resp.get_data(as_text=True)
        if 'data-role-injected-v29' in t: return resp
        role = session.get('role', '')
        cls = 'role-admin' if role=='admin' else ('role-guest' if role=='guest' else 'role-anon')
        css = """<style id="role-guest-css-v29">
body.role-guest .btn-danger,
body.role-guest [onclick*="elete"],
body.role-guest [onclick*="eleteOrder"],
body.role-guest [onclick*="eleteScheme"],
body.role-guest [onclick*="eleteDevice"],
body.role-guest [data-admin-only],
body.role-guest a[href="/admin"]{ display:none !important; }
body.role-guest .admin-badge::after{ content:" · 👁 только просмотр"; color:#c0392b; font-size:11px; }
</style>"""
        import re as _re
        t = _re.sub(r'<body([^>]*)>', '<body\\1 class="'+cls+'" data-role-injected-v29="1">', t, count=1)
        t = t.replace('</head>', css + '</head>', 1)
        resp.set_data(t)
    except Exception: pass
    return resp


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    FIXES.append('inject role class v29'); print('  ok: inject role class v29')

# === 6. Проверка и запись ===
try:
    ast.parse(src)
    print('  ok: ast.parse swh.py')
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v29_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))

open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v29', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v29. Правок:', len(FIXES), '| бэкап: backups/swh_pre_v29_' + TS + '.py')
