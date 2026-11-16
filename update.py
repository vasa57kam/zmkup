import ast, json, os, re, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v19_' + TS + '.py')
src = open('swh.py', encoding='utf-8').read()
FIXES = []

# ---------- 1) Топология + чистка карты (сервер) ----------
if "'/api/topology'" not in src:
    EP = '''
def _ip_of(s):
    m = re.search(r'(\\d{1,3}\\.){3}\\d{1,3}', s or '')
    return m.group(0) if m else ''

def _short_name(name):
    parts = (name or '').split(' --- ')
    if len(parts) >= 2:
        base = parts[0]
        for pref in ('Хотьково, ', 'Сергиев Посад, ', 'Сергиев Посад-6, '):
            base = base.replace(pref, '')
        return (base + ' · ' + parts[1])[:48]
    return (name or '')[:48]

def _topo_data(conn):
    devs = conn.execute('SELECT * FROM network_devices ORDER BY id').fetchall()
    by_ip, by_name = {}, {}
    dups, junk = [], []
    for d in devs:
        ip = (d['ip_address'] or '').strip()
        if not re.fullmatch(r'(\\d{1,3}\\.){3}\\d{1,3}', ip):
            junk.append(d['id'])
            continue
        if ip in by_ip:
            dups.append(d['id'])
        else:
            by_ip[ip] = d
        by_name[d['name']] = d
    nodes = {}
    for ip, d in by_ip.items():
        nodes[d['id']] = {'id': d['id'], 'ip': ip, 'name': d['name'], 'short': _short_name(d['name']),
                          'location': d['location'] or '', 'model': d['model'] or '', 'level': 4}
    edges, seen = [], set()
    def add_edge(pid, cid, pp, cp):
        if pid in nodes and cid in nodes and pid != cid and (pid, cid) not in seen:
            seen.add((pid, cid))
            edges.append({'from': pid, 'to': cid, 'from_port': pp or '', 'to_port': cp or ''})
    for c in conn.execute('SELECT * FROM map_connections').fetchall():
        add_edge(c['from_device_id'], c['to_device_id'], c['from_port'], c['to_port'])
    orders = {o['id']: o for o in conn.execute('SELECT * FROM work_orders').fetchall()}
    for l in conn.execute('SELECT * FROM links').fetchall():
        o = orders.get(l['order_id'])
        if not o:
            continue
        my_ip = (o['new_switch_ip'] or o['old_switch_ip'] or '').strip()
        me = by_ip.get(my_ip)
        up = by_name.get(l['upstream_device']) or by_ip.get(_ip_of(l['upstream_device']))
        if not me or not up:
            continue
        if l['link_type'] == 'uplink':
            add_edge(up['id'], me['id'], l['upstream_port'], l['old_port'])
        else:
            add_edge(me['id'], up['id'], l['old_port'], l['upstream_port'])
    children = {}
    has_parent = set()
    for e in edges:
        children.setdefault(e['from'], []).append(e['to'])
        has_parent.add(e['to'])
    roots = [i for i in nodes if i not in has_parent]
    core = [i for i in roots if 'ядра' in (nodes[i]['name'] or '').lower() or nodes[i]['ip'].startswith('10.163.100.')]
    queue = [(i, 0) for i in (core or roots)]
    seenlvl = set()
    while queue:
        i, lv = queue.pop(0)
        if i in seenlvl:
            continue
        seenlvl.add(i)
        nodes[i]['level'] = lv
        for ch in children.get(i, []):
            queue.append((ch, lv + 1))
    return {'nodes': list(nodes.values()), 'edges': edges, 'duplicates': dups, 'junk': junk}

@app.route('/api/topology')
def topology_api():
    conn = get_db()
    t = _topo_data(conn)
    conn.close()
    return jsonify(t)

@app.route('/api/admin/map_cleanup', methods=['POST'])
def map_cleanup():
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    base = os.path.dirname(os.path.abspath(__file__))
    shutil.copyfile(os.path.join(base, 'switch_replacements.db'),
                    os.path.join(base, 'backups', 'db_pre_cleanup_' + datetime.now().strftime('%Y%m%d_%H%M%S') + '.db'))
    conn = get_db()
    t = _topo_data(conn)
    merged = 0
    for dup_id in t['duplicates']:
        dup = conn.execute('SELECT * FROM network_devices WHERE id=?', (dup_id,)).fetchone()
        keep = conn.execute('SELECT * FROM network_devices WHERE ip_address=? ORDER BY id LIMIT 1', (dup['ip_address'],)).fetchone()
        if not keep or keep['id'] == dup_id:
            continue
        conn.execute('UPDATE links SET upstream_device=? WHERE upstream_device=?', (keep['name'], dup['name']))
        conn.execute('UPDATE map_connections SET from_device_id=? WHERE from_device_id=?', (keep['id'], dup_id))
        conn.execute('UPDATE map_connections SET to_device_id=? WHERE to_device_id=?', (keep['id'], dup_id))
        conn.execute('UPDATE port_marks SET device_id=? WHERE device_id=?', (keep['id'], dup_id))
        conn.execute('DELETE FROM network_devices WHERE id=?', (dup_id,))
        merged += 1
    junked = 0
    for jid in t['junk']:
        conn.execute('DELETE FROM network_devices WHERE id=?', (jid,))
        junked += 1
    for n in t['nodes']:
        loc = n['location']
        if not loc:
            parts = (n['name'] or '').split(' --- ')
            loc = ' --- '.join(parts[:2]) if len(parts) >= 2 else (n['name'] or '')
        conn.execute('UPDATE network_devices SET location=? WHERE id=?', (loc, n['id']))
    parent = {}
    for e in t['edges']:
        parent.setdefault(e['to'], e['from'])
    for nid, pid in parent.items():
        conn.execute('UPDATE network_devices SET parent_device_id=? WHERE id=?', (pid, nid))
    levels = {}
    for n in t['nodes']:
        levels.setdefault(n['level'], []).append(n['id'])
    for lv, ids in levels.items():
        for i, nid in enumerate(sorted(ids)):
            conn.execute('UPDATE network_devices SET position_x=?, position_y=? WHERE id=?',
                         (80 + i * 230, 60 + lv * 190, nid))
    conn.commit()
    t2 = _topo_data(conn)
    conn.close()
    return jsonify({'ok': True, 'merged': merged, 'junk': junked, 'edges': len(t2['edges']), 'levels': len(levels)})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + EP + src[idx:]
    FIXES.append('topology+cleanup'); print('  ok: /api/topology + /api/admin/map_cleanup')

# ---------- 2) Инъекция блоков на страницы (без якорей в HTML) ----------
if 'def inject_page_extras' not in src:
    EP = '''
TOPO_SECTION = """<div id="topoSection" class="map-container">
<h3>🌳 Топология сети — кто от кого</h3>
<input id="topoQ" placeholder="🔍 поиск устройства (улица, IP, подъезд)..." oninput="topoSearch()" style="padding:.5rem;width:280px;">
<button class="btn btn-primary" onclick="topoCleanup()">🧹 Автоукладка + чистка</button>
<button class="btn btn-secondary" onclick="topoLegacy()">📇 Редактор портов</button>
<span id="topoStats" style="margin-left:8px;color:#7f8c8d;"></span>
<div id="topoCanvas" style="height:560px;background:#fff;border:1px solid #ddd;border-radius:8px;margin-top:8px;"></div>
<div id="topoInfo" style="margin-top:8px;background:#fff;padding:10px;border-radius:8px;"></div>
<div style="margin-top:6px;font-size:13px;color:#7f8c8d;">Цвета: 🔴 ядро · 🟠 агрегация · 🔵 доступ · 🟢 ниже · ⚪ без связей. Стрелка родитель→потомок, подпись — порты. Клик по узлу — панель устройства.</div>
</div>"""

@app.after_request
def inject_page_extras(resp):
    try:
        if 'text/html' not in (resp.content_type or ''):
            return resp
        t = resp.get_data(as_text=True)
        changed = False
        if request.path == '/map' and 'id="topoSection"' not in t and '<div class="container">' in t:
            t = t.replace('<div class="container">', '<div class="container">' + TOPO_SECTION, 1)
            t = t.replace('</body>', '<script src="/static/topo.js?v=1"></script></body>', 1)
            changed = True
        if request.path in ('/commands', '/gen') and 'id="cmdLib"' not in t:
            t = t.replace('</body>', '<div id="cmdLib" style="margin:10px;"></div><script src="/static/lib.js?v=1"></script></body>', 1)
            changed = True
        if changed:
            resp.set_data(t)
    except Exception:
        pass
    return resp


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + EP + src[idx:]
    FIXES.append('page extras'); print('  ok: инъекция топологии и справочника')

# ---------- 3) topo.js ----------
TOPO_JS = r'''
(function(){
  var net=null, NODES=[];
  function el(id){ return document.getElementById(id); }
  function load(){
    fetch('/api/topology').then(function(r){return r.json();}).then(function(t){
      NODES=t.nodes;
      var cols=['#c0392b','#e67e22','#2980b9','#27ae60','#95a5a6'];
      var nodes=new vis.DataSet(t.nodes.map(function(n){
        return {id:n.id, label:n.short+'\n'+n.ip, shape:'box', margin:8,
          color:{background:cols[Math.min(n.level,4)], border:'#2c3e50'},
          font:{color:'#fff', size:13},
          title:n.name+'\n📍 '+(n.location||'—')+'\n'+(n.model||'модель не указана'), level:n.level};
      }));
      var edges=new vis.DataSet(t.edges.map(function(e,i){
        return {id:i, from:e.from, to:e.to, arrows:'to',
          label:(e.from_port||'?')+'→'+(e.to_port||'?'),
          color:{color:'#7f8c8d'}, font:{size:11, align:'middle'},
          smooth:{type:'cubicBezier', forceDirection:'vertical'}};
      }));
      net=new vis.Network(el('topoCanvas'), {nodes:nodes, edges:edges}, {
        layout:{hierarchical:{direction:'UD', sortMethod:'directed', levelSeparation:150, nodeSpacing:180, treeSpacing:230}},
        physics:false, interaction:{hover:true, tooltipDelay:120}, edges:{width:2}});
      net.on('click', function(p){ if(p.nodes.length){ showInfo(p.nodes[0]); } });
      el('topoStats').textContent='Устройств: '+t.nodes.length+' · связей: '+t.edges.length+' · дублей: '+(t.duplicates||[]).length+' · мусора: '+(t.junk||[]).length;
    }).catch(function(e){ el('topoStats').textContent='Ошибка загрузки топологии: '+e.message; });
  }
  function showInfo(id){
    var n=null; NODES.forEach(function(x){ if(x.id===id)n=x; });
    if(!n) return;
    el('topoInfo').innerHTML='<b>'+n.name+'</b><br>IP: '+n.ip+' · '+(n.model||'модель ?')+'<br>📍 '+(n.location||'—')+'<br>'
      +'<button class="btn btn-primary" onclick="topoSsh(\''+n.ip+'\')">🖥️ SSH / Тулза</button> '
      +'<button class="btn btn-secondary" onclick="topoGen(\''+n.ip+'\')">🧬 Генератор команд</button>';
  }
  window.topoSsh=function(ip){ sessionStorage.setItem('toolz_tgt',ip); sessionStorage.setItem('toolz_tool','ssh'); location.href='/tools'; };
  window.topoGen=function(ip){ sessionStorage.setItem('gen_ip',ip); location.href='/gen'; };
  window.topoSearch=function(){
    var q=(el('topoQ').value||'').toLowerCase(); if(!q) return;
    var n=null; NODES.forEach(function(x){ if(!n && (x.name+' '+x.ip+' '+(x.location||'')).toLowerCase().indexOf(q)>=0) n=x; });
    if(n&&net){ net.focus(n.id,{scale:1.1,animation:true}); net.selectNodes([n.id]); showInfo(n.id); }
  };
  window.topoCleanup=function(){
    if(!confirm('Автоукладка + чистка: склеить дубли по IP, убрать мусор, расставить по уровням? (БД будет сохранена в backups)')) return;
    fetch('/api/admin/map_cleanup',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({pin:localStorage.getItem('swhpin')||prompt('PIN:')||''})})
    .then(function(r){return r.json();}).then(function(res){
      alert(res.ok? ('Готово: дублей склеено '+res.merged+', мусора убрано '+res.junk+', связей '+res.edges+', уровней '+res.levels) : ('Ошибка: '+(res.error||'')));
      load();
    });
  };
  window.topoLegacy=function(){ var l=el('legacyMap'); if(l){ l.style.display=(l.style.display==='none')?'':'none'; } };
  document.addEventListener('DOMContentLoaded', function(){
    var c=document.querySelector('.container'), sec=el('topoSection');
    if(c&&sec){
      var leg=document.createElement('div'); leg.id='legacyMap'; leg.style.display='none';
      while(c.children.length>1){ leg.appendChild(c.children[1]); }
      c.appendChild(leg);
    }
    load();
  });
})();
'''
open('static/topo.js', 'w').write(TOPO_JS)
print('  ok: static/topo.js')

# ---------- 4) lib.js — поиск по справочнику команд ----------
LIB_JS = r'''
(function(){
  var ROWS=[], chip='';
  function esc(s){ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function render(){
    var box=document.getElementById('cmdLib'); if(!box) return;
    var q=(document.getElementById('libQ')||{}).value||''; q=q.toLowerCase();
    var cats=[]; ROWS.forEach(function(r){ if(r.category && cats.indexOf(r.category)<0) cats.push(r.category); });
    var f=ROWS.filter(function(r){
      if(chip && r.category!==chip) return false;
      if(!q) return true;
      return ((r.title||'')+' '+(r.body||'')+' '+(r.category||'')+' '+(r.notes||'')).toLowerCase().indexOf(q)>=0;
    });
    box.innerHTML='<div class="card" style="background:#fff;padding:12px;border-radius:10px;margin:10px 0;">'
      +'<b>📚 Справочник команд — поиск</b> <input id="libQ" value="'+esc(q)+'" placeholder="vlan, камера, ism, dgs, des, порты, ddm..." style="padding:8px;width:300px;" oninput="libRender()">'
      +'<div style="margin:6px 0;"><button class="btn btn-secondary" style="padding:4px 10px;" onclick="libChip(\'\')">Все</button>'
      +cats.map(function(c){ return '<button class="btn '+(chip===c?'btn-primary':'btn-secondary')+'" style="padding:4px 10px;" onclick="libChip(\''+esc(c)+'\')">'+esc(c)+'</button>'; }).join('')
      +'</div><div>Найдено: '+f.length+'</div>'
      +f.map(function(r){
        return '<div style="border:1px solid #ddd;border-radius:8px;padding:10px;margin:8px 0;background:#fafafa;">'
          +'<b>'+esc(r.title)+'</b> <span class="badge" style="background:#1565c0;color:#fff;border-radius:10px;padding:2px 8px;font-size:12px;">'+esc(r.category||'')+'</span><br>'
          +'<pre style="white-space:pre-wrap;font-family:monospace;background:#111;color:#0f0;padding:8px;border-radius:6px;margin:6px 0;">'+esc(r.body)+'</pre>'
          +(r.notes? '<div style="color:#7f8c8d;font-size:13px;">'+esc(r.notes)+'</div>':'')
          +'<button class="btn btn-primary" style="padding:4px 10px;" onclick="libCopy(this)" data-b="'+esc(r.body)+'">📋 Копировать</button> '
          +'<button class="btn btn-success" style="padding:4px 10px;" onclick="libTools(this)" data-b="'+esc(r.body)+'">▶ В Тулзу (SSH)</button></div>';
      }).join('')+'</div>';
  }
  window.libRender=render;
  window.libChip=function(c){ chip=c; render(); };
  window.libCopy=function(b){ navigator.clipboard.writeText(b.dataset.b); alert('Скопировано'); };
  window.libTools=function(b){ sessionStorage.setItem('gen2tools', b.dataset.b); location.href='/tools'; };
  fetch('/api/commands').then(function(r){return r.json();}).then(function(rows){ ROWS=rows||[]; render(); });
})();
'''
open('static/lib.js', 'w').write(LIB_JS)
print('  ok: static/lib.js')

# ---------- 5) Пакеты команд в справочник ----------
import sqlite3
conn = sqlite3.connect('switch_replacements.db')
conn.execute('CREATE TABLE IF NOT EXISTS commands_dict (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, body TEXT, notes TEXT)')
PACKS = [
 ('DGS-1210/ME: создать VLAN', 'DGS-1210/ME', 'vlan database\nvlan 135\nexit\ncopy running-config startup-config', 'Cisco-подобный CLI DGS-1210 ME'),
 ('DGS-1210/ME: камера БР на VLAN (комбо)', 'DGS-1210/ME', 'vlan database\nvlan 135\nexit\ninterface ethernet 1/0/26-28\nvlan participation include 135\nvlan tagging tagged\nexit\ninterface ethernet 1/0/21\nvlan participation include 135\nvlan pvid 135\nexit\ncopy running-config startup-config', 'Магистрали tagged + порт камеры untagged/pvid'),
 ('DGS-1210/ME: убрать порт из VLAN', 'DGS-1210/ME', 'interface ethernet 1/0/21\nvlan participation exclude 135\nexit\ncopy running-config startup-config', ''),
 ('DGS-1210/ME: порты/ошибки/скорость', 'DGS-1210/ME', 'show interface ethernet 1/0/21\nshow interface ethernet 1/0/21 counters\ninterface ethernet 1/0/21\nspeed 100\nexit\ncopy running-config startup-config', ''),
 ('DGS-1210/ME: MAC и лог', 'DGS-1210/ME', 'show bridge mac-address-table\nshow log', ''),
 ('DES-3200: создать VLAN + камера БР (комбо)', 'DES-3200', 'create vlan OTS.INTERCOM.UFA.PRV tag 135\nconfig vlan vlanid 135 add tagged 26-28\nconfig vlan vlanid 135 add untagged 21\nconfig ports 21 pvid 135\nsave', 'Как в боевой инструкции: имя+tag, магистрали tagged, камера untagged+pvid'),
 ('DES-3200: убрать порт из VLAN', 'DES-3200', 'config vlan vlanid 135 delete 21\nsave', ''),
 ('DES-3200: ISM смена source-порта (безопасно)', 'DES-3200', 'config igmp_snooping multicast_vlan vlan1151 delete member_port 28\nconfig igmp_snooping multicast_vlan vlan1151 delete tag_member_port 28\nconfig igmp_snooping multicast_vlan vlan1151 delete source_port 27\nconfig igmp_snooping multicast_vlan vlan1151 add source_port 28\nconfig igmp_snooping multicast_vlan vlan1151 add member_port 27\nshow igmp_snooping multicast_vlan\nsave', 'Source в ISM VLAN всегда ОДИН; патч-корд переставить физически после add source_port'),
 ('DES-3200: магистраль→абонент без ошибок ISM', 'DES-3200', 'config igmp_snooping multicast_vlan vlan1151 delete tag_member_port 25\nconfig igmp_snooping multicast_vlan vlan1151 add member_port 25\nconfig vlan vlanid 1 delete 25\nconfig vlan vlanid 135 add untagged 25\nconfig ports 25 pvid 135\nsave', 'Сначала ISM-роли, потом VLAN-ы'),
 ('DES-3200: порты/ошибки/DDM/лог', 'DES-3200', 'show ports 21\nshow counters ports 21\nshow ddm ports 26\nshow utilization ports 26-28\nshow log', ''),
]
added = 0
for title, cat, body, notes in PACKS:
    r = conn.execute('SELECT id FROM commands_dict WHERE title=?', (title,)).fetchone()
    if not r:
        conn.execute('INSERT INTO commands_dict (title, category, body, notes) VALUES (?,?,?,?)', (title, cat, body, notes))
        added += 1
conn.commit(); conn.close()
FIXES.append('command packs +' + str(added)); print('  ok: пакеты команд добавлено', added)

# ---------- 6) gen.js: быстрые сценарии + фильтр операций ----------
gp = 'static/gen.js'
g = open(gp, encoding='utf-8').read()
if 'window.preset' not in g:
    g += r'''
(function(){
  function ins(){
    var fam=document.getElementById('fam'); if(!fam) return;
    var row=document.createElement('div'); row.style.margin='6px 0';
    row.innerHTML='<b>⚡ Быстрые сценарии:</b> '
      +'<button class="btn" style="background:#16a085;" onclick="preset(\'create\')">🆕 Создать VLAN</button> '
      +'<button class="btn" style="background:#8e44ad;" onclick="preset(\'cam\')">📹 Камера БР (комбо)</button> '
      +'<button class="btn" style="background:#c0392b;" onclick="preset(\'ism_swap\')">🔁 ISM: смена source</button> '
      +'<button class="btn" style="background:#d35400;" onclick="preset(\'t2a\')">🔧 Магистраль→абонент</button> '
      +'<button class="btn" style="background:#2980b9;" onclick="preset(\'ddm\')">🔦 DDM оптики</button> '
      +'<button class="btn" style="background:#7f8c8d;" onclick="preset(\'show_log\')">📜 show log</button>';
    fam.parentNode.insertBefore(row, fam);
    var f=document.createElement('input'); f.id='opFilter';
    f.placeholder='🔍 фильтр операций: vlan, ism, порт, ddm...';
    f.style.cssText='width:280px;padding:6px;margin:6px 0;';
    f.oninput=function(){ renderOps(); };
    var op=document.getElementById('op'); op.parentNode.insertBefore(f, op);
    var ip=sessionStorage.getItem('gen_ip');
    if(ip){ sessionStorage.removeItem('gen_ip'); var e=document.getElementById('ip'); if(e){ e.value=ip; } }
  }
  window.renderOps=function(){
    var fam=document.getElementById('fam').value, op=document.getElementById('op');
    var q=((document.getElementById('opFilter')||{}).value||'').toLowerCase();
    var keys=Object.keys(TPL[fam]||{}).filter(function(k){
      return !q || (NAMES[k]||k).toLowerCase().indexOf(q)>=0 || k.indexOf(q)>=0;
    });
    op.innerHTML=keys.map(function(k){ return '<option value="'+k+'">'+(NAMES[k]||k)+'</option>'; }).join('');
    fillTpl();
  };
  var _sf=setFam;
  setFam=function(){ _sf(); if(document.getElementById('opFilter')){ renderOps(); } };
  window.preset=function(k){
    var fl=document.getElementById('opFilter'); if(fl){ fl.value=''; }
    renderOps();
    if(k==='ism_swap'||k==='t2a'){ document.getElementById('v').value='1151'; }
    if(k==='create'||k==='cam'){ document.getElementById('v').value='135'; }
    var op=document.getElementById('op'); op.value=k; fillTpl(); gen();
  };
  if(document.readyState!=='loading'){ ins(); } else { document.addEventListener('DOMContentLoaded', ins); }
})();
'''
    open(gp, 'w').write(g)
    FIXES.append('gen presets+filter'); print('  ok: gen.js сценарии+фильтр')
new_src, n = re.subn(r'/static/gen\.js\?v=\d+', '/static/gen.js?v=19', src)
if n:
    src = new_src; FIXES.append('gen v19')

# ---------- 7) Штамп + проверка + запись ----------
try:
    ast.parse(src)
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v19_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v19', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v19. Правок:', len(FIXES), '| бэкап: backups/swh_pre_v19_' + TS + '.py')
