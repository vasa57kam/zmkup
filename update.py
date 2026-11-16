import ast, json, os, re, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v31_' + TS + '.py')
src = open('swh.py', encoding='utf-8').read()
FIXES = []

# === 1. Создание таблицы guest_permissions (если её нет) ===
try:
    import sqlite3
    c = sqlite3.connect('switch_replacements.db')
    c.execute('CREATE TABLE IF NOT EXISTS guest_permissions (key TEXT PRIMARY KEY, val INTEGER DEFAULT 0)')
    c.commit(); c.close()
    FIXES.append('DB table guest_permissions')
    print('  ok: таблица guest_permissions')
except Exception as e:
    print('  DB err:', e)

# === 2. Блок кода с правами гостя (добавляем перед if __name__) ===
if 'GP_DEFAULTS_V31' not in src:
    block = '''
# --- GP_DEFAULTS_V31 ---
GP_DEFAULTS_V31 = {
    'can_view_orders':1,'can_create_orders':0,'can_edit_orders':0,
    'can_view_map':1,'can_edit_map':0,
    'can_view_vlans':1,'can_view_kb':1,'can_view_gen':1,'can_view_tools':1,
    'can_view_inventory':1,'can_edit_inventory':0,
    'can_view_schemes':1,'can_edit_schemes':0,
    'can_view_stock':1,'can_view_field':1,'can_view_netlab':1,
    'can_edit_attachments':0,'can_edit_notes':0,'can_edit_fdb':0,
}
def _gp_v31(key, default=None):
    if default is None: default = GP_DEFAULTS_V31.get(key, 0)
    try:
        import sqlite3 as _s3
        c = _s3.connect('switch_replacements.db')
        r = c.execute("SELECT val FROM guest_permissions WHERE key=?", (key,)).fetchone()
        if r is None:
            c.execute("INSERT INTO guest_permissions (key,val) VALUES (?,?)", (key, int(default)))
            c.commit(); c.close(); return int(default)
        c.close(); return int(r[0])
    except Exception: return int(default)

def _gp_set_v31(key, val):
    try:
        import sqlite3 as _s3
        c = _s3.connect('switch_replacements.db')
        c.execute("INSERT OR REPLACE INTO guest_permissions (key,val) VALUES (?,?)", (key, int(bool(val))))
        c.commit(); c.close()
    except Exception: pass

@app.route('/api/admin/guest_perms_v31', methods=['GET','POST'])
def admin_guest_perms_v31():
    if session.get('role') != 'admin':
        return jsonify({'error':'admin only'}), 403
    if request.method == 'GET':
        return jsonify({k: _gp_v31(k) for k in GP_DEFAULTS_V31})
    d = request.json or {}
    k = d.get('key')
    if k not in GP_DEFAULTS_V31: return jsonify({'error':'unknown'}), 400
    _gp_set_v31(k, d.get('val'))
    return jsonify({'ok':True})


'''
    idx = src.rfind("if __name__ == '__main__':")
    if idx >= 0:
        src = src[:idx] + block + src[idx:]
        FIXES.append('GP code block'); print('  ok: блок прав гостя добавлен')
    else:
        print('  ПРОПУСК: if __name__ не найден')

# === 3. UI-блок прав в /admin (добавляем перед закрывающим div) ===
if 'id="guestPermsBlock_v31"' not in src:
    ui = '''<div class="card" id="guestPermsBlock_v31" style="background:#fff;padding:1rem;border-radius:8px;margin:1rem 0;">
<h3>👁 Права гостевого доступа</h3>
<p style="color:#7f8c8d;">DELETE и /admin/* запрещены гостю навсегда.</p>
<div style="columns:2;gap:20px;font-size:14px;" id="gpList_v31">
<label><input type="checkbox" data-gp="can_view_orders"> смотреть наряды</label><br>
<label><input type="checkbox" data-gp="can_create_orders"> создавать наряды</label><br>
<label><input type="checkbox" data-gp="can_edit_orders"> редактировать наряды</label><br>
<label><input type="checkbox" data-gp="can_view_map"> смотреть карту</label><br>
<label><input type="checkbox" data-gp="can_edit_map"> редактировать карту</label><br>
<label><input type="checkbox" data-gp="can_view_vlans"> VLAN</label><br>
<label><input type="checkbox" data-gp="can_view_kb"> база знаний</label><br>
<label><input type="checkbox" data-gp="can_view_gen"> генератор</label><br>
<label><input type="checkbox" data-gp="can_view_tools"> SSH</label><br>
<label><input type="checkbox" data-gp="can_view_inventory"> склад</label><br>
<label><input type="checkbox" data-gp="can_edit_inventory"> редактировать склад</label><br>
<label><input type="checkbox" data-gp="can_view_schemes"> схемы</label><br>
<label><input type="checkbox" data-gp="can_edit_schemes"> редактировать схемы</label><br>
<label><input type="checkbox" data-gp="can_view_stock"> резерв</label><br>
<label><input type="checkbox" data-gp="can_view_field"> полевые</label><br>
<label><input type="checkbox" data-gp="can_view_netlab"> NetLab</label><br>
</div>
<div id="gpMsg_v31" style="margin-top:8px;color:#27ae60;font-size:13px;"></div>
</div>
<script>
(function(){
  var list=document.getElementById('gpList_v31'); if(!list) return;
  fetch('/api/admin/guest_perms_v31').then(function(r){return r.json();}).then(function(perms){
    Array.prototype.forEach.call(list.querySelectorAll('[data-gp]'), function(cb){
      cb.checked = !!perms[cb.dataset.gp];
      cb.onchange = function(){
        fetch('/api/admin/guest_perms_v31',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({key:cb.dataset.gp, val:cb.checked?1:0})})
        .then(function(r){return r.json();}).then(function(res){
          var m=document.getElementById('gpMsg_v31');
          if(m){ m.textContent = res.ok? '✓ сохранено' : ('ошибка'); setTimeout(function(){m.textContent='';},2000); }
        });
      };
    });
  });
})();
</script>
'''
    # Ищем закрывающий div админки
    if '<div class="container">' in src:
        idx = src.rfind('</div>\n</div>\n</body>')
        if idx > 0:
            src = src[:idx] + ui + src[idx:]
            FIXES.append('UI block'); print('  ok: UI блок прав добавлен')
        else:
            print('  ПРОПУСК: закрывающий div не найден')

# === 4. Inject скрытия опасных кнопок для гостя ===
if 'guest_hide_js_v31' not in src:
    ep = '''
@app.after_request
def _guest_hide_v31(resp):
    try:
        if session.get('role') != 'guest': return resp
        if 'text/html' not in (resp.content_type or ''): return resp
        t = resp.get_data(as_text=True)
        if 'guest_hide_js_v31' in t: return resp
        js = "<script id='guest_hide_js_v31'>function _gh(){document.querySelectorAll('.btn-danger,[onclick*=\"elete\"]')\n.forEach(function(e){e.style.display='none';});}\ndocument.addEventListener('DOMContentLoaded',_gh);\nnew MutationObserver(_gh).observe(document.documentElement,{childList:true,subtree:true});</script>"
        t = t.replace('</body>', js + '</body>', 1)
        resp.set_data(t)
    except Exception: pass
    return resp


'''
    idx = src.rfind("if __name__ == '__main__':")
    if idx >= 0:
        src = src[:idx] + ep + src[idx:]
        FIXES.append('hide dangerous buttons'); print('  ok: скрытие опасных кнопок')

# === 5. Проверка синтаксиса ===
try:
    ast.parse(src)
    print('  ok: ast.parse прошёл')
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v31_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))

# === 6. Запись ===
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v31', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v31. Правок:', len(FIXES), '| бэкап: backups/swh_pre_v31_' + TS + '.py')
