import ast, json, os, re, shutil, sqlite3
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v20_' + TS + '.py')
src = open('swh.py', encoding='utf-8').read()
FIXES = []
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); FIXES.append(label); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) КРИТИЧНО: import re (из-за него /api/topology падал с 500)
if not re.search(r'^import re$', src, re.M):
    rep('import json\n', 'import json\nimport re\n', 'import re')

# 2) Журнал изменений
if "'/api/changelog'" not in src:
    ep = '''
@app.route('/api/changelog')
def changelog_api():
    conn = get_db()
    try:
        rows = conn.execute('SELECT * FROM change_log ORDER BY id DESC LIMIT 200').fetchall()
    except Exception:
        rows = []
    conn.close()
    return jsonify([dict(r) for r in rows])


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    FIXES.append('changelog'); print('  ok: /api/changelog')

# 3) Порты камер из базы для команды «ОТС камеры»
if "'/api/ots_cam_ports'" not in src:
    ep = '''
@app.route('/api/ots_cam_ports')
def ots_cam_ports():
    ip = (request.args.get('ip') or '').strip()
    conn = get_db()
    ports, cams = [], []
    try:
        for c in conn.execute('SELECT * FROM cameras').fetchall():
            sw = (c['switch_name'] or '')
            if ip and ip not in sw:
                continue
            p = (c['switch_port'] or '').strip()
            if p:
                ports.append(p)
                cams.append({'ip': c['ip'], 'port': p, 'zone': c['zone'] or '', 'sw': sw})
    except Exception:
        pass
    try:
        q = conn.execute('SELECT s.*, o.old_switch_ip oip, o.new_switch_ip nip FROM subscribers s JOIN work_orders o ON o.id=s.order_id WHERE s.is_camera=1').fetchall()
        for s in q:
            if ip and ip not in (s['oip'] or '') and ip not in (s['nip'] or ''):
                continue
            p = str(s['new_port'] or s['old_port'] or '').strip()
            if p and p != '0':
                ports.append(p)
                cams.append({'ip': s['ip_address'], 'port': p, 'zone': s['address'] or '', 'sw': ip})
    except Exception:
        pass
    try:
        dev = conn.execute('SELECT id FROM network_devices WHERE ip_address=?', (ip,)).fetchone() if ip else None
        if dev:
            for m in conn.execute("SELECT * FROM port_marks WHERE device_id=? AND port_type='camera'", (dev['id'],)).fetchall():
                ports.append(str(m['port']))
                cams.append({'ip': m['mac'] or '', 'port': str(m['port']), 'zone': m['label'] or '', 'sw': ip})
    except Exception:
        pass
    conn.close()
    seen, uniq = set(), []
    for p in ports:
        if p not in seen:
            seen.add(p); uniq.append(p)
    return jsonify({'ports': uniq, 'cams': cams})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    FIXES.append('ots_cam_ports'); print('  ok: /api/ots_cam_ports')

# 4) Инъекция: /map без container + глобальный редизайн
rep("""        if request.path == '/map' and 'id="topoSection"' not in t and '<div class="container">' in t:
            t = t.replace('<div class="container">', '<div class="container">' + TOPO_SECTION, 1)
            t = t.replace('</body>', '<script src="/static/topo.js?v=1"></script></body>', 1)
            changed = True""",
"""        if request.path == '/map' and 'id="topoSection"' not in t:
            t = t.replace('</body>', TOPO_SECTION + '<script src="/static/topo.js?v=2"></script></body>', 1)
            changed = True
        if 'id="ui20"' not in t and '</head>' in t:
            t = t.replace('</head>', '<style id="ui20">' + UI20_CSS + '</style></head>', 1)
            changed = True""", 'инъекция /map + редизайн')

if 'UI20_CSS = ' not in src:
    CSS = '''UI20_CSS = """
:root{--bg:#eef2f7;--ink:#1f2d3d;--mut:#7b8a9a;--acc:#2563eb;--rad:12px}
body{background:var(--bg)!important;color:var(--ink);font-family:'Segoe UI',system-ui,Arial,sans-serif!important}
.navbar{position:sticky;top:0;z-index:60;box-shadow:0 2px 12px rgba(0,0,0,.18);flex-wrap:wrap;gap:.4rem;padding:.7rem 1.2rem!important}
.nav-links{flex-wrap:wrap;gap:.3rem!important}
.nav-link{border-radius:8px;padding:.35rem .65rem!important;font-size:.9rem}
.nav-link:hover{background:rgba(255,255,255,.16)!important}
.container{max-width:1520px!important;padding:1.1rem!important}
.card,.order-card,.info-card,.map-container,.map-controls,.modal-content{border-radius:var(--rad)!important;box-shadow:0 4px 14px rgba(31,45,61,.08)!important;border:1px solid #e6ecf4}
.btn{border-radius:9px!important;font-weight:600;transition:transform .12s,box-shadow .12s}
.btn:hover{transform:translateY(-1px);box-shadow:0 4px 10px rgba(0,0,0,.16)}
input,select,textarea{border-radius:8px!important;border:1px solid #d6dfe9!important;padding:.5rem!important;background:#fff}
input:focus,select:focus,textarea:focus{outline:2px solid rgba(37,99,235,.30);border-color:var(--acc)!important}
select{max-width:100%}
.data-table th{background:#334155!important}
.data-table tr:nth-child(even){background:#f8fafc}
.data-table td,.data-table th{padding:.6rem .8rem!important}
pre{border-radius:8px}
.modal-content{max-width:880px!important;width:94%;max-height:88vh;overflow-y:auto}
.uplink-field{flex-wrap:wrap;align-items:center}
.uplink-field select{flex:2;min-width:230px}
.orders-grid{gap:1rem!important}
.order-card h3{font-size:1.05rem}
h1,h2,h3{color:var(--ink)}
.badge{border-radius:8px}
#topoCanvas{border-radius:12px;border:1px solid #e6ecf4!important}
#topoSection{background:#fff;border-radius:12px;padding:12px;margin-bottom:12px;box-shadow:0 4px 14px rgba(31,45,61,.08)}
"""

'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + CSS + src[idx:]
    FIXES.append('UI20 CSS'); print('  ok: глобальный редизайн')

# 5) topo.js v2: работает и на standalone /map
TOPO_JS = r'''
(function(){
  var net=null, NODES=[];
  function el(id){ return document.getElementById(id); }
  function load(){
    fetch('/api/topology').then(function(r){ if(!r.ok){ throw new Error('HTTP '+r.status); } return r.json(); }).then(function(t){
      NODES=t.nodes||[];
      var cols=['#c0392b','#e67e22','#2980b9','#27ae60','#95a5a6'];
      var nodes=new vis.DataSet(NODES.map(function(n){
        return {id:n.id, label:n.short+'\n'+n.ip, shape:'box', margin:10,
          color:{background:cols[Math.min(n.level,4)], border:'#22303f'},
          font:{color:'#fff', size:13, face:'Segoe UI'},
          title:n.name+'\n📍 '+(n.location||'—')+'\n'+(n.model||'модель не указана'), level:n.level};
      }));
      var edges=new vis.DataSet((t.edges||[]).map(function(e,i){
        return {id:i, from:e.from, to:e.to, arrows:'to',
          label:(e.from_port||'?')+'→'+(e.to_port||'?'),
          color:{color:'#8fa2b5'}, font:{size:11, align:'middle', color:'#5b6b7c'},
          smooth:{type:'cubicBezier', forceDirection:'vertical'}};
      }));
      net=new vis.Network(el('topoCanvas'), {nodes:nodes, edges:edges}, {
        layout:{hierarchical:{direction:'UD', sortMethod:'directed', levelSeparation:150, nodeSpacing:190, treeSpacing:240}},
        physics:false, interaction:{hover:true, tooltipDelay:120, navigationButtons:true, keyboard:true}, edges:{width:2}});
      net.on('click', function(p){ if(p.nodes.length){ showInfo(p.nodes[0]); } });
      el('topoStats').textContent='Устройств: '+NODES.length+' · связей: '+(t.edges||[]).length+' · дублей: '+(t.duplicates||[]).length+' · мусора: '+(t.junk||[]).length;
    }).catch(function(e){ el('topoStats').textContent='⚠️ Топология не загрузилась: '+e.message+' (обновите страницу / примените v20)'; });
  }
  function showInfo(id){
    var n=null; NODES.forEach(function(x){ if(x.id===id)n=x; });
    if(!n) return;
    el('topoInfo').innerHTML='<b>'+n.name+'</b><br>IP: '+n.ip+' · '+(n.model||'модель ?')+'<br>📍 '+(n.location||'—')+'<br>'
      +'<button class="btn btn-primary" onclick="topoSsh(\''+n.ip+'\')">🖥️ SSH / Тулза</button> '
      +'<button class="btn btn-secondary" onclick="topoGen(\''+n.ip+'\')">🧬 Генератор</button> '
      +'<button class="btn btn-success" onclick="topoOts(\''+n.ip+'\')">📹 ОТС камеры (из базы)</button>';
  }
  window.topoSsh=function(ip){ sessionStorage.setItem('toolz_tgt',ip); sessionStorage.setItem('toolz_tool','ssh'); location.href='/tools'; };
  window.topoGen=function(ip){ sessionStorage.setItem('gen_ip',ip); location.href='/gen'; };
  window.topoOts=function(ip){ sessionStorage.setItem('gen_ip',ip); sessionStorage.setItem('gen_preset','ots_db'); location.href='/gen'; };
  window.topoSearch=function(){
    var q=(el('topoQ').value||'').toLowerCase(); if(!q) return;
    var n=null; NODES.forEach(function(x){ if(!n && (x.name+' '+x.ip+' '+(x.location||'')).toLowerCase().indexOf(q)>=0) n=x; });
    if(n&&net){ net.focus(n.id,{scale:1.1,animation:true}); net.selectNodes([n.id]); showInfo(n.id); }
  };
  window.topoCleanup=function(){
    if(!confirm('Автоукладка + чистка: склеить дубли по IP, убрать мусор, расставить по уровням? (бэкап БД будет сохранён)')) return;
    fetch('/api/admin/map_cleanup',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({pin:localStorage.getItem('swhpin')||prompt('PIN:')||''})})
    .then(function(r){return r.json();}).then(function(res){
      alert(res.ok? ('Готово: дублей склеено '+res.merged+', мусора убрано '+res.junk+', связей '+res.edges+', уровней '+res.levels) : ('Ошибка: '+(res.error||'')));
      load();
    });
  };
  window.topoLegacy=function(){ var l=el('legacyMap'); if(l){ l.style.display=(l.style.display==='none')?'':'none'; } };
  function mount(){
    var sec=el('topoSection'); if(!sec) return;
    var c=document.querySelector('.container')||document.body;
    if(sec.parentNode!==c){ c.insertBefore(sec, c.firstChild); }
    else if(c.firstChild!==sec){ c.insertBefore(sec, c.firstChild); }
    var leg=document.createElement('div'); leg.id='legacyMap'; leg.style.display='none';
    Array.prototype.slice.call(c.children).forEach(function(ch){
      if(ch!==sec && ch.tagName!=='SCRIPT'){ leg.appendChild(ch); }
    });
    c.appendChild(leg);
    load();
  }
  if(document.readyState!=='loading'){ mount(); } else { document.addEventListener('DOMContentLoaded', mount); }
})();
'''
open('static/topo.js', 'w').write(TOPO_JS)
FIXES.append('topo.js v2'); print('  ok: topo.js v2')

# 6) gen.js: ОТС камеры + новые операции + кнопка «из базы»
gp = 'static/gen.js'
g = open(gp, encoding='utf-8').read()
if 'ots_cam' not in g:
    g += r'''
(function(){
  TPL.des.ots_cam='create vlan OTS.INTERCOM.UFA.PRV tag {vlan}\nconfig vlan vlanid {vlan} add tagged {trunk}\nconfig vlan vlanid {vlan} add untagged {ports}\nconfig ports {ports} pvid {vlan}\nsave';
  TPL.dgs.ots_cam='vlan database\nvlan {vlan}\nexit\ninterface ethernet 1/0/{trunk}\nvlan participation include {vlan}\nvlan tagging tagged\nexit\ninterface ethernet 1/0/{ports}\nvlan participation include {vlan}\nvlan pvid {vlan}\nexit\ncopy running-config startup-config';
  TPL.des.show_vlan_all='show vlan';
  TPL.des.port_desc='config ports {ports} description {text}';
  TPL.des.loopdetect='config loopdetect ports {ports} state enabled';
  TPL.des.igmp_on='config igmp_snooping state enable';
  TPL.des.show_run='show config current';
  TPL.dgs.show_vlan_all='show vlan';
  TPL.dgs.show_run='show running-config';
  NAMES.ots_cam='📹 ОТС камеры: VLAN 135 + магистрали + камеры из базы';
  NAMES.show_vlan_all='Показать все VLAN';
  NAMES.port_desc='Описание порта (description)';
  NAMES.loopdetect='Включить loopdetect на портах';
  NAMES.igmp_on='Включить IGMP snooping globally';
  NAMES.show_run='Показать текущий конфиг';
  HINTS.ots_cam='VLAN=135; Порт(ы) магистрали — транки (26-28); Порт(ы) — порты камер. Кнопка «📹 ОТС камеры (из базы)» сама подставит порты камер из БД по IP свитча.';
  HINTS.port_desc='Порт(ы) — порты; Текст — описание (напр. camera-6 / abon-12).';
  HINTS.loopdetect='Порт(ы) — абонентские порты для защиты от петель.';
  HINTS.show_run='Ничего вводить не надо.';
  MEMO.ots_cam='1) create vlan OTS.INTERCOM.UFA.PRV tag 135\n2) магистрали tagged\n3) порты камер untagged (из базы)\n4) pvid камерам\n5) save\n6) проверить поток каждой камеры';
  function addBtn(){
    var fam=document.getElementById('fam'); if(!fam) return;
    var row=document.createElement('div'); row.style.margin='6px 0';
    row.innerHTML='<button class="btn" style="background:#0e9f6e;" onclick="otsFromDb()">📹 ОТС камеры (из базы)</button> '
      +'<span style="color:#7b8a9a;font-size:13px;">подставит порты камер из БД по IP свитча (поле IP)</span>';
    fam.parentNode.insertBefore(row, fam.nextSibling);
  }
  window.otsFromDb=function(){
    var ipEl=document.getElementById('ip');
    var ip=(ipEl&&ipEl.value)||prompt('IP свитча (камеры из базы):','');
    if(!ip) return;
    if(ipEl){ ipEl.value=ip; }
    fetch('/api/ots_cam_ports?ip='+encodeURIComponent(ip)).then(function(r){return r.json();}).then(function(res){
      var ports=(res.ports||[]);
      if(!ports.length){ alert('В базе нет камер для '+ip+'. Введите порты вручную.'); }
      document.getElementById('v').value='135';
      var tr=document.getElementById('tr'); if(tr && !tr.value){ tr.value='26-28'; }
      if(ports.length){ document.getElementById('p').value=ports.join(','); }
      var fl=document.getElementById('opFilter'); if(fl){ fl.value=''; }
      if(window.renderOps){ renderOps(); }
      document.getElementById('op').value='ots_cam';
      fillTpl(); gen();
      if(ports.length){ alert('Камер из базы: '+ports.length+' → порты '+ports.join(',')); }
    }).catch(function(e){ alert('Ошибка: '+e.message); });
  };
  function boot(){
    addBtn();
    var pr=sessionStorage.getItem('gen_preset');
    if(pr==='ots_db'){ sessionStorage.removeItem('gen_preset'); setTimeout(otsFromDb, 300); }
  }
  if(document.readyState!=='loading'){ boot(); } else { document.addEventListener('DOMContentLoaded', boot); }
})();
'''
    open(gp, 'w').write(g)
    FIXES.append('gen ots_cam+new ops'); print('  ok: gen.js ОТС камеры + новые операции')
new_src, n = re.subn(r'/static/gen\.js\?v=\d+', '/static/gen.js?v=20', src)
if n:
    src = new_src; FIXES.append('gen v20')

# 7) Команда «ОТС камеры» в справочник (примечание: камера из базы)
conn = sqlite3.connect('switch_replacements.db')
conn.execute('CREATE TABLE IF NOT EXISTS commands_dict (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, body TEXT, notes TEXT)')
TITLE = 'ОТС камеры (VLAN 135 + магистрали + порты камер из базы)'
if not conn.execute('SELECT id FROM commands_dict WHERE title=?', (TITLE,)).fetchone():
    conn.execute('INSERT INTO commands_dict (title, category, body, notes) VALUES (?,?,?,?)', (
        TITLE, 'DES-3200',
        'create vlan OTS.INTERCOM.UFA.PRV tag 135\nconfig vlan vlanid 135 add tagged 26-28\nconfig vlan vlanid 135 add untagged <порты камер>\nconfig ports <порты камер> pvid 135\nsave',
        'камера из базы: порты камер берутся из БД (cameras / subscribers is_camera / port_marks) кнопкой «📹 ОТС камеры (из базы)» в генераторе или на карте'))
    conn.commit()
    FIXES.append('cmd ОТС камеры'); print('  ok: команда ОТС камеры в справочнике')
conn.close()

# 8) Штамп + проверка + запись
try:
    ast.parse(src)
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v20_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v20', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v20. Правок:', len(FIXES), '| бэкап: backups/swh_pre_v20_' + TS + '.py')
