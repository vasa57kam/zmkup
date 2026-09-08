import os, re, ast, sqlite3
src = open('swh.py').read()

pat = re.compile(r'(?:<div style="margin-bottom:1rem;">\s*<input id="orderSearch"[^>]*>\s*</div>\s*)+', re.S)
def _one(m):
    b = m.group(0)
    if b.count('orderSearch') > 1:
        return b.split('</div>')[0] + '</div>\n'
    return b
src = pat.sub(_one, src, count=1)
print('поисков стало:', src.count('id="orderSearch"'))

if 'id="closeBtn"' not in src:
    anchor = '<div id="orderDetails"></div>'
    block = '''<div class="header-actions" style="margin-bottom:1rem;">
    <button id="closeBtn" class="btn btn-success" onclick="toggleOrderStatus()">✅ Закрыть наряд</button>
    <a class="btn btn-secondary" href="/api/report/{{ order_id }}" target="_blank">📄 Отчёт</a>
    <a href="/planner/{{ order_id }}" class="btn btn-primary">🗺️ Планировщик</a>
    <a href="/fdb/{{ order_id }}" class="btn btn-success">📊 FDB</a>
</div>
<div id="orderDetails"></div>'''
    if anchor in src:
        src = src.replace(anchor, block, 1)
        print('ok: кнопки наряда')

if 'function toggleOrderStatus' not in src:
    anchor2 = 'loadOrder();\nloadSteps();'
    js = '''var orderStatus='created';
function toggleOrderStatus(){
  var ns=(orderStatus==='closed')?'created':'closed';
  var msg=(ns==='closed')?'Закрыть наряд?':'Открыть наряд снова?';
  if(!confirm(msg)) return;
  fetch('/api/orders/'+orderId,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:ns})}).then(function(){location.reload();});
}
function refreshCloseBtn(){
  fetch('/api/orders/'+orderId).then(function(r){return r.json();}).then(function(o){
    orderStatus=o.status||'created';
    var h=document.querySelector('.page-header h1');
    if(h){h.textContent='📋 Наряд №'+(o.order_number||orderId)+' '+(orderStatus==='closed'?'🔒 закрыт':'');}
    var b=document.getElementById('closeBtn');
    if(!b) return;
    if(orderStatus==='closed'){b.textContent='↩️ Открыть снова';b.className='btn btn-secondary';}
    else{b.textContent='✅ Закрыть наряд';b.className='btn btn-success';}
  });
}
loadOrder();
loadSteps();
refreshCloseBtn();'''
    if anchor2 in src:
        src = src.replace(anchor2, js, 1)
        print('ok: JS закрытия')

conn = sqlite3.connect('switch_replacements.db')
conn.execute('''CREATE TABLE IF NOT EXISTS commands_dict (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, category TEXT, body TEXT, notes TEXT)''')
for col, typ in (('commands_used', 'TEXT'), ('vehicle_needed', 'INTEGER DEFAULT 0')):
    try:
        conn.execute('ALTER TABLE work_orders ADD COLUMN ' + col + ' ' + typ)
    except Exception:
        pass
conn.commit()
conn.close()
print('ok: БД команд')

if 'def auto_flags' not in src:
    helper = '''
def auto_flags(order_id):
    conn = get_db()
    o = conn.execute('SELECT * FROM work_orders WHERE id=?', (order_id,)).fetchone()
    oldc = conn.execute("SELECT COUNT(*) c FROM fdb_tables WHERE order_id=? AND switch_type='old'", (order_id,)).fetchone()['c']
    newc = conn.execute("SELECT COUNT(*) c FROM fdb_tables WHERE order_id=? AND switch_type='new'", (order_id,)).fetchone()['c']
    oldcam = conn.execute("SELECT COUNT(*) c FROM fdb_tables WHERE order_id=? AND switch_type='old' AND vlan LIKE '%135%'", (order_id,)).fetchone()['c']
    newcam = conn.execute("SELECT COUNT(*) c FROM fdb_tables WHERE order_id=? AND switch_type='new' AND vlan LIKE '%135%'", (order_id,)).fetchone()['c']
    ups = conn.execute("SELECT * FROM links WHERE order_id=? AND link_type='uplink'", (order_id,)).fetchall()
    dls = conn.execute("SELECT * FROM links WHERE order_id=? AND link_type='downlink'", (order_id,)).fetchall()
    subs = conn.execute('SELECT * FROM subscribers WHERE order_id=?', (order_id,)).fetchall()
    inv = conn.execute('SELECT * FROM switch_inventory', ()).fetchall()
    conn.close()
    old_ip = (o['old_switch_ip'] or '') if o else ''
    f = {}
    f[0] = bool(o and o['old_switch_ip'] and o['old_switch_model'])
    f[1] = oldc > 0
    f[2] = len(ups) > 0 or len(dls) > 0
    f[3] = False
    f[4] = False
    f[5] = False
    f[6] = len(ups) > 0 and all(u['new_port'] for u in ups)
    f[7] = len(dls) > 0 and all(d['new_port'] for d in dls)
    f[8] = (len(subs) == 0) or all(s['new_port'] for s in subs)
    f[9] = newc > 0
    f[10] = oldc > 0 and newc > 0
    f[11] = (oldcam == 0) or (newcam > 0)
    f[12] = False
    f[13] = any(i['last_ip'] == old_ip and i['status'] in ('reset_done', 'in_stock', 'written_off') for i in inv)
    f[14] = any(i['last_ip'] == old_ip and i['status'] in ('in_stock', 'written_off') for i in inv)
    return f

'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + helper + src[idx:]
    print('ok: auto_flags')

i = src.find('def get_steps(order_id):')
if i >= 0 and 'auto_flags' not in src[i:i+900]:
    j = src.find('return jsonify([dict(r) for r in rows])', i)
    if j >= 0 and j - i < 900:
        old_ret = 'return jsonify([dict(r) for r in rows])'
        merged = '''rows = [dict(r) for r in rows]
    fl = auto_flags(order_id)
    for k, r in enumerate(rows):
        if fl.get(k):
            r['done'] = 1
    return jsonify(rows)'''
        src = src[:j] + merged + src[j+len(old_ret):]
        print('ok: этапы с авто-галками')

old_rep = "        mark = '[x]' if s['done'] else '[ ]'"
if old_rep in src:
    ir = src.find('def order_report(order_id):')
    if ir >= 0:
        old_loop = '    for s in steps:'
        jl = src.find(old_loop, ir)
        if jl >= 0 and jl - ir < 5000:
            src = src[:jl] + '    fl = auto_flags(order_id)\n    for k, s in enumerate(steps):' + src[jl+len(old_loop):]
            jm = src.find(old_rep, jl)
            if jm >= 0 and jm - jl < 800:
                src = src[:jm] + "        mark = '[x]' if (s['done'] or fl.get(k)) else '[ ]'" + src[jm+len(old_rep):]
                print('ok: отчёт с авто-этапами')

ir = src.find('def order_report(order_id):')
ja = src.find("    text = '\\n'.join(L)", ir)
if ja >= 0 and 'ИСПОЛЬЗОВАННЫЕ КОМАНДЫ' not in src[ir:ja]:
    add = '''    L.append('')
    L.append('ИСПОЛЬЗОВАННЫЕ КОМАНДЫ: ' + (o['commands_used'] or 'не указаны'))
    L.append('НУЖНА БЫЛА МАШИНА: ' + ('ДА' if o['vehicle_needed'] else 'нет'))
'''
    src = src[:ja] + add + src[ja:]
    print('ok: команды в отчёте')

old_f = "    for f in ('status','old_switch_ip','new_switch_ip','old_switch_location'):"
new_f = "    for f in ('status','old_switch_ip','new_switch_ip','old_switch_location','commands_used','vehicle_needed'):"
if old_f in src:
    src = src.replace(old_f, new_f, 1)
    print('ok: PUT наряда расширен')

if "'/commands'" not in src:
    cmds = '''CMD_HTML = """{% extends "base.html" %}
{% block title %}Справочник команд{% endblock %}
{% block content %}
<div class="page-header">
    <h1>📚 Справочник команд</h1>
</div>
<div style="background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;">
<h3>➕ Добавить команду</h3>
<div class="form-row">
<div class="form-group"><label>Название:</label><input id="cmdTitle"></div>
<div class="form-group"><label>Категория:</label><input id="cmdCat" placeholder="волокно / LAN / uplink..."></div>
</div>
<div class="form-group"><label>Команда / порядок действий:</label><textarea id="cmdBody" style="width:100%;height:90px;font-family:monospace;"></textarea></div>
<div class="form-group"><label>Примечание:</label><input id="cmdNotes"></div>
<button class="btn btn-primary" onclick="addCmd()">💾 Сохранить</button>
</div>
<div id="cmdList"></div>
{% endblock %}
{% block scripts %}
<script>
function loadCmds(){
  fetch('/api/commands').then(function(r){return r.json();}).then(function(rows){
    var h='';
    rows.forEach(function(c){
      h+='<div style="background:#fff;padding:.8rem;margin:.4rem 0;border-radius:8px;">';
      h+='<b>'+c.title+'</b> <span class="badge badge-ok">'+(c.category||'')+'</span> ';
      h+='<button class="btn btn-danger" style="padding:2px 8px;" data-id="'+c.id+'" onclick="delCmd(this.dataset.id)">🗑</button>';
      h+='<pre style="background:#f4f6f7;padding:.5rem;margin:.5rem 0;white-space:pre-wrap;">'+(c.body||'')+'</pre>';
      if(c.notes){h+='<small style="color:#7f8c8d;">'+c.notes+'</small>';}
      h+='</div>';
    });
    document.getElementById('cmdList').innerHTML=h||'<p>Справочник пуст</p>';
  });
}
function addCmd(){
  var b={title:document.getElementById('cmdTitle').value,
    category:document.getElementById('cmdCat').value,
    body:document.getElementById('cmdBody').value,
    notes:document.getElementById('cmdNotes').value};
  fetch('/api/commands',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(loadCmds);
}
function delCmd(id){
  if(!confirm('Удалить команду?')) return;
  fetch('/api/commands/'+id,{method:'DELETE'}).then(loadCmds);
}
loadCmds();
</script>
{% endblock %}"""

@app.route('/commands')
def commands_page():
    return render_template_string(CMD_HTML)

@app.route('/api/commands', methods=['GET'])
def get_commands():
    conn = get_db()
    rows = conn.execute('SELECT * FROM commands_dict ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/commands', methods=['POST'])
def add_command():
    d = request.json or {}
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO commands_dict (title, category, body, notes) VALUES (?,?,?,?)',
        (d.get('title',''), d.get('category',''), d.get('body',''), d.get('notes','')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/commands/<int:cmd_id>', methods=['DELETE'])
def del_command(cmd_id):
    conn = get_db()
    conn.execute('DELETE FROM commands_dict WHERE id=?', (cmd_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + cmds + src[idx:]
    old_nav = '<a href="/map" class="nav-link">🗺️ Карта сети</a>'
    if old_nav in src:
        src = src.replace(old_nav, old_nav + '\n            <a href="/commands" class="nav-link">📚 Команды</a>', 1)
    print('ok: справочник команд')

if 'id="cmdUsedBox"' not in src:
    anchor3 = '<h3>Абоненты</h3>'
    block3 = '''<h3>📚 Команды и ресурсы</h3>
<div style="background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;">
    <div id="cmdUsedBox"></div>
    <div class="form-group"><label>Использованные команды (можно править руками):</label>
        <textarea id="cmdsUsed" style="width:100%;height:70px;"></textarea></div>
    <label><input type="checkbox" id="vehNeed"> Нужна была машина (вышка/авто)</label>
    <button class="btn btn-primary" onclick="saveCmds()">💾 Сохранить</button>
</div>
<h3>Абоненты</h3>'''
    if anchor3 in src:
        src = src.replace(anchor3, block3, 1)
    js3 = '''function loadCmdsUsed(){
  fetch('/api/commands').then(function(r){return r.json();}).then(function(rows){
    var h='';
    rows.forEach(function(c){
      h+='<label style="display:block;margin:.2rem 0;"><input type="checkbox" class="cmdPick" value="'+c.title+'"> '+c.title+' <small style="color:#7f8c8d;">('+(c.category||'')+')</small></label>';
    });
    document.getElementById('cmdUsedBox').innerHTML=h||'<small>Справочник пуст — добавьте на странице «Команды»</small>';
  });
  fetch('/api/orders/'+orderId).then(function(r){return r.json();}).then(function(o){
    document.getElementById('cmdsUsed').value=o.commands_used||'';
    document.getElementById('vehNeed').checked=!!o.vehicle_needed;
    var used=(o.commands_used||'').split(';');
    document.querySelectorAll('.cmdPick').forEach(function(cb){
      if(used.indexOf(cb.value)>=0){cb.checked=true;}
    });
  });
}
function saveCmds(){
  var picks=[];
  document.querySelectorAll('.cmdPick').forEach(function(cb){ if(cb.checked){picks.push(cb.value);} });
  var extra=document.getElementById('cmdsUsed').value;
  var merged=picks.join('; ');
  if(extra && merged.indexOf(extra)<0){ merged=merged? merged+'; '+extra : extra; }
  var body={commands_used:merged, vehicle_needed:document.getElementById('vehNeed').checked?1:0};
  fetch('/api/orders/'+orderId,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(){alert('Сохранено');});
}
'''
    target = 'refreshCloseBtn();'
    i4 = src.find(target)
    if i4 >= 0 and 'loadCmdsUsed' not in src[max(0,i4-3000):i4]:
        src = src[:i4] + js3 + 'loadCmdsUsed();\n' + src[i4:]
        print('ok: блок команд в наряде')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, всё цело')