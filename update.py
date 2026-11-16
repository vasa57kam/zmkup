import ast, json, os, re, shutil, sqlite3
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v21_' + TS + '.py')
src = open('swh.py', encoding='utf-8').read()
FIXES = []
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); FIXES.append(label); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Таблица схем + API
conn = sqlite3.connect('switch_replacements.db')
conn.execute('''CREATE TABLE IF NOT EXISTS net_schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, data TEXT, updated_at TEXT)''')
conn.commit(); conn.close()
if "'/api/schemes'" not in src:
    EP = '''
@app.route('/netlab')
def netlab_page():
    return render_template_string(NETLAB_HTML)

@app.route('/api/schemes', methods=['GET', 'POST'])
def schemes_api():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('SELECT id, name, updated_at FROM net_schemes ORDER BY id DESC').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        conn.close()
        return jsonify({'error': 'pin'}), 403
    c = conn.cursor()
    c.execute('INSERT INTO net_schemes (name, data, updated_at) VALUES (?,?,?)',
              (d.get('name', 'Схема'), d.get('data', '{}'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    i = c.lastrowid
    conn.close()
    return jsonify({'ok': True, 'id': i})

@app.route('/api/schemes/<int:sid>', methods=['GET', 'PUT', 'DELETE'])
def scheme_item(sid):
    conn = get_db()
    if request.method == 'GET':
        r = conn.execute('SELECT * FROM net_schemes WHERE id=?', (sid,)).fetchone()
        conn.close()
        if not r:
            return jsonify({'error': 'nf'}), 404
        return jsonify(dict(r))
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        conn.close()
        return jsonify({'error': 'pin'}), 403
    if request.method == 'DELETE':
        conn.execute('DELETE FROM net_schemes WHERE id=?', (sid,))
        conn.commit(); conn.close()
        return jsonify({'ok': True})
    conn.execute('UPDATE net_schemes SET name=?, data=?, updated_at=? WHERE id=?',
                 (d.get('name', 'Схема'), d.get('data', '{}'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), sid))
    conn.commit(); conn.close()
    return jsonify({'ok': True})


NETLAB_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🎨 Схемы / NetLab</title>
<style>
body{font-family:'Segoe UI',Arial;font-size:15px;margin:0;background:#eef2f7;color:#1f2d3d}
#nlTop{background:#2c3e50;color:#fff;padding:8px 12px;display:flex;gap:6px;flex-wrap:wrap;align-items:center;position:sticky;top:0;z-index:10}
#nlTop button{padding:7px 12px;border:none;border-radius:8px;cursor:pointer;font-weight:600}
#nlWrap{display:flex;gap:8px;padding:8px;height:calc(100vh - 52px)}
#nlPal{width:150px;background:#fff;border-radius:12px;padding:8px;overflow-y:auto;box-shadow:0 4px 14px rgba(31,45,61,.08)}
#nlPal button{display:block;width:100%;margin:4px 0;padding:8px;border:1px solid #e9eef5;border-radius:8px;background:#f8fafc;cursor:pointer;text-align:left}
#nlPal button:hover{background:#e8f0fe}
#nlCanvasBox{flex:1;background:#fff;border-radius:12px;position:relative;overflow:hidden;box-shadow:0 4px 14px rgba(31,45,61,.08)}
#nlCanvas{width:100%;height:100%;cursor:grab}
#nlSide{width:300px;background:#fff;border-radius:12px;padding:10px;overflow-y:auto;box-shadow:0 4px 14px rgba(31,45,61,.08)}
#nlSide input,#nlSide select{width:100%;padding:6px;margin:3px 0;border:1px solid #d6dfe9;border-radius:6px}
#nlLog{background:#111;color:#0f0;font-family:monospace;font-size:12px;height:160px;overflow-y:auto;border-radius:8px;padding:6px;margin-top:8px;white-space:pre-wrap}
.nlLbl{font-size:12px;fill:#5b6b7c}
@media print{#nlTop,#nlPal,#nlSide{display:none}#nlWrap{height:auto}#nlCanvasBox{box-shadow:none}}
</style></head>
<body>
<div id="nlTop">
<b>🎨 NetLab — схемы ЛВС + симуляция</b>
<button style="background:#27ae60;color:#fff" onclick="nlSave()">💾 Сохранить</button>
<button style="background:#3498db;color:#fff" onclick="nlList()">📂 Открыть</button>
<button style="background:#8e44ad;color:#fff" onclick="nlExport('svg')">⬇ SVG</button>
<button style="background:#8e44ad;color:#fff" onclick="nlExport('png')">⬇ PNG</button>
<button style="background:#7f8c8d;color:#fff" onclick="window.print()">🖨️</button>
<button style="background:#e67e22;color:#fff" onclick="nlTool('link')">🔗 Соединить</button>
<button style="background:#95a5a6;color:#fff" onclick="nlTool('select')">🖱 Выбор</button>
<button style="background:#e74c3c;color:#fff" onclick="nlDel()">🗑 Удалить</button>
<span id="nlHint" style="font-size:12px;opacity:.85">выбор/перетаскивание · колесо=зум · фон=панорама</span>
</div>
<div id="nlWrap">
<div id="nlPal"></div>
<div id="nlCanvasBox"><svg id="nlCanvas"><g id="nlWorld"></g></svg></div>
<div id="nlSide">
<b>Свойства</b><div id="nlProps"><i>выберите устройство или линию</i></div>
<hr><b>📡 Симуляция трафика</b>
Источник: <select id="simSrc"></select>
Приёмник: <select id="simDst"></select>
Режим: <select id="simMode"><option value="unicast">unicast (A→B)</option><option value="multicast">multicast (камера→viewers)</option><option value="broadcast">broadcast / flood</option></select>
VLAN: <input id="simVlan" value="135">
<button style="background:#27ae60;color:#fff;padding:8px 14px;border:none;border-radius:8px;cursor:pointer" onclick="nlSim()">▶ Пуск</button>
<button style="background:#95a5a6;color:#fff;padding:8px 14px;border:none;border-radius:8px;cursor:pointer" onclick="nlStop()">⏹ Стоп</button>
<div id="nlLog"></div>
</div>
</div>
<script src="/static/netlab.js?v=1"></script>
</body></html>"""
'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + EP + src[idx:]
    FIXES.append('netlab api+page'); print('  ok: /netlab + /api/schemes')

NL_LINK = '<a href="/netlab" class="nav-link">🎨 Схемы</a>'
if NL_LINK not in src:
    rep('<a href="/kb" class="nav-link">📖 База знаний</a>',
        '<a href="/kb" class="nav-link">📖 База знаний</a>\n            ' + NL_LINK, 'nav netlab')

# 2) netlab.js — редактор + симулятор
NLJS = r'''
(function(){
var TYPES={switch:{i:'🖧',c:'#2980b9',n:'Коммутатор'},core:{i:'🌐',c:'#c0392b',n:'Ядро/роутер'},olt:{i:'🏢',c:'#8e44ad',n:'OLT'},split:{i:'🌳',c:'#16a085',n:'Сплиттер PON'},onu:{i:'📡',c:'#0e9f6e',n:'ONU/ONT'},camera:{i:'📹',c:'#d35400',n:'IP-камера'},pc:{i:'🖥️',c:'#34495e',n:'ПК/терминал'},server:{i:'🗄️',c:'#2c3e50',n:'Сервер/NVR'},ap:{i:'📶',c:'#2980b9',n:'AP'},printer:{i:'🖨️',c:'#7f8c8d',n:'Принтер'}};
var S={devices:[],links:[],nid:1,lid:1};
var sel=null, selLink=null, tool='select', connectFrom=null;
var view={x:0,y:0,k:1}, drag=null, pan=null, timers=[];
function el(id){return document.getElementById(id);}
function svg(){return el('nlCanvas');}
function world(){return el('nlWorld');}
function log(t){var l=el('nlLog'); l.textContent+=t+'\n'; l.scrollTop=l.scrollHeight;}
function vcolor(v){var h=(parseInt(v)||0)*47%360; return 'hsl('+h+',75%,50%)';}
function dev(id){return S.devices.find(function(d){return d.id===id;});}
function render(){
  var w=world(); var h='';
  S.links.forEach(function(L){
    var a=dev(L.a), b=dev(L.b); if(!a||!b) return;
    var col=L.media==='fiber'?'#f59e0b':(L.media==='pon'?'#10b981':'#64748b');
    var mx=(a.x+b.x)/2, my=(a.y+b.y)/2;
    h+='<line data-l="'+L.id+'" x1="'+a.x+'" y1="'+a.y+'" x2="'+b.x+'" y2="'+b.y+'" stroke="'+(selLink===L.id?'#e74c3c':col)+'" stroke-width="'+(selLink===L.id?4:2.5)+'" style="cursor:pointer"/>';
    h+='<text class="nlLbl" x="'+mx+'" y="'+(my-6)+'" text-anchor="middle">'+(L.pa||'?')+'→'+(L.pb||'?')+' · '+(L.mode==='trunk'?'trunk['+L.vlans+']':'acc'+L.vlans)+' · '+L.media+'</text>';
  });
  S.devices.forEach(function(d){
    var t=TYPES[d.type]||TYPES.switch;
    h+='<g data-d="'+d.id+'" style="cursor:move">';
    h+='<rect x="'+(d.x-46)+'" y="'+(d.y-30)+'" width="92" height="60" rx="10" fill="'+t.c+'" stroke="'+(sel===d.id?'#e74c3c':'#22303f')+'" stroke-width="'+(sel===d.id?3:1.5)+'"/>';
    h+='<text x="'+d.x+'" y="'+(d.y-8)+'" text-anchor="middle" font-size="18">'+t.i+'</text>';
    h+='<text x="'+d.x+'" y="'+(d.y+8)+'" text-anchor="middle" font-size="11" fill="#fff">'+(d.name||t.n).slice(0,16)+'</text>';
    h+='<text x="'+d.x+'" y="'+(d.y+22)+'" text-anchor="middle" font-size="10" fill="#e8eef5">'+(d.ip||'')+(d.vlan?' v'+d.vlan:'')+'</text>';
    h+='</g>';
  });
  w.innerHTML=h;
  w.setAttribute('transform','translate('+view.x+','+view.y+') scale('+view.k+')');
  fillSimSelects();
}
function fillSimSelects(){
  var opts=S.devices.map(function(d){return '<option value="'+d.id+'">'+(d.name||TYPES[d.type].n)+' ('+(d.ip||d.id)+')</option>';}).join('');
  var a=el('simSrc'), b=el('simDst'); var av=a.value, bv=b.value;
  a.innerHTML=opts; b.innerHTML=opts; if(av)a.value=av; if(bv)b.value=bv;
}
function palette(){
  el('nlPal').innerHTML=Object.keys(TYPES).map(function(k){
    return '<button onclick="nlAdd(\''+k+'\')">'+TYPES[k].i+' '+TYPES[k].n+'</button>';
  }).join('')+'<hr><button onclick="nlDemo()">📦 Пример: камера+PON</button>';
}
window.nlAdd=function(k){
  S.devices.push({id:S.nid++, type:k, x:200+Math.random()*400, y:150+Math.random()*300, name:'', ip:'', vlan:(k==='camera'||k==='pc'||k==='onu')?'135':'', model:''});
  render();
};
window.nlTool=function(t){ tool=t; connectFrom=null; el('nlHint').textContent = t==='link'? 'кликните устройство A, затем B' : 'выбор/перетаскивание · колесо=зум · фон=панорама'; };
window.nlDel=function(){
  if(selLink!=null){ S.links=S.links.filter(function(L){return L.id!==selLink;}); selLink=null; }
  else if(sel!=null){ S.links=S.links.filter(function(L){return L.a!==sel&&L.b!==sel;}); S.devices=S.devices.filter(function(d){return d.id!==sel;}); sel=null; }
  props(); render();
};
function props(){
  var p=el('nlProps');
  if(selLink!=null){
    var L=S.links.find(function(x){return x.id===selLink;});
    p.innerHTML='<b>Линия #'+L.id+'</b> порт A:<input value="'+(L.pa||'')+'" oninput="nlLinkSet('+L.id+',\'pa\',this.value)"> порт B:<input value="'+(L.pb||'')+'" oninput="nlLinkSet('+L.id+',\'pb\',this.value)"> режим:<select onchange="nlLinkSet('+L.id+',\'mode\',this.value)"><option value="trunk"'+(L.mode==='trunk'?' selected':'')+'>trunk</option><option value="access"'+(L.mode==='access'?' selected':'')+'>access</option></select> VLAN-ы:<input value="'+(L.vlans||'')+'" oninput="nlLinkSet('+L.id+',\'vlans\',this.value)"> среда:<select onchange="nlLinkSet('+L.id+',\'media\',this.value)"><option value="copper"'+(L.media==='copper'?' selected':'')+'>медь</option><option value="fiber"'+(L.media==='fiber'?' selected':'')+'>оптика</option><option value="pon"'+(L.media==='pon'?' selected':'')+'>PON</option></select>';
    return;
  }
  if(sel!=null){
    var d=dev(sel);
    p.innerHTML='<b>'+TYPES[d.type].i+' '+TYPES[d.type].n+'</b> имя:<input value="'+(d.name||'')+'" oninput="nlDevSet('+d.id+',\'name\',this.value)"> IP:<input value="'+(d.ip||'')+'" oninput="nlDevSet('+d.id+',\'ip\',this.value)"> access-VLAN:<input value="'+(d.vlan||'')+'" oninput="nlDevSet('+d.id+',\'vlan\',this.value)"> модель:<input value="'+(d.model||'')+'" oninput="nlDevSet('+d.id+',\'model\',this.value)">';
    return;
  }
  p.innerHTML='<i>выберите устройство или линию</i>';
}
window.nlDevSet=function(id,f,v){ var d=dev(id); if(d){ d[f]=v; render(); } };
window.nlLinkSet=function(id,f,v){ var L=S.links.find(function(x){return x.id===id;}); if(L){ L[f]=v; render(); } };
function pt(e){ var r=svg().getBoundingClientRect(); return {x:(e.clientX-r.left-view.x)/view.k, y:(e.clientY-r.top-view.y)/view.k}; }
svg().addEventListener('mousedown', function(e){
  var g=e.target.closest('[data-d]'); var l=e.target.closest('[data-l]');
  if(g){ var id=+g.dataset.d;
    if(tool==='link'){ if(connectFrom==null){ connectFrom=id; log('🔗 от устройства #'+id+' → кликните второе'); }
      else if(connectFrom!==id){ S.links.push({id:S.lid++, a:connectFrom, b:id, pa:'', pb:'', mode:'trunk', vlans:'135,1151', media:'copper'}); connectFrom=null; tool='select'; render(); }
      return; }
    sel=id; selLink=null; props(); var p=pt(e); var d=dev(id); drag={id:id, dx:p.x-d.x, dy:p.y-d.y}; render(); return; }
  if(l){ selLink=+l.dataset.l; sel=null; props(); render(); return; }
  sel=null; selLink=null; props(); pan={x:e.clientX-view.x, y:e.clientY-view.y}; render();
});
window.addEventListener('mousemove', function(e){
  if(drag){ var p=pt(e); var d=dev(drag.id); if(d){ d.x=p.x-drag.dx; d.y=p.y-drag.dy; render(); } }
  else if(pan){ view.x=e.clientX-pan.x; view.y=e.clientY-pan.y; render(); }
});
window.addEventListener('mouseup', function(){ drag=null; pan=null; });
svg().addEventListener('wheel', function(e){ e.preventDefault(); var f=e.deltaY<0?1.1:0.9; view.k=Math.max(0.3,Math.min(3,view.k*f)); render(); }, {passive:false});
// ---- симуляция ----
function allows(L, v){
  var list=String(L.vlans||'').split(',').map(function(x){return x.trim();});
  if(L.mode==='trunk') return list.indexOf(String(v))>=0;
  return String(L.vlans)===String(v);
}
function neighbors(id, v){
  var out=[];
  S.links.forEach(function(L){
    if(L.a===id && allows(L,v)) out.push({to:L.b, L:L, dir:'ab'});
    if(L.b===id && allows(L,v)) out.push({to:L.a, L:L, dir:'ba'});
  });
  return out;
}
function path(src, dst, v){
  var prev={}, seen={}, q=[src]; seen[src]=true;
  while(q.length){
    var cur=q.shift();
    if(cur===dst) break;
    neighbors(cur,v).forEach(function(n){ if(!seen[n.to]){ seen[n.to]=true; prev[n.to]={from:cur, L:n.L}; q.push(n.to); } });
  }
  if(!seen[dst]) return null;
  var hops=[], cur=dst;
  while(cur!==src){ var p=prev[cur]; hops.unshift({from:p.from, to:cur, L:p.L}); cur=p.from; }
  return hops;
}
function animate(hops, v, label){
  var col=vcolor(v);
  hops.forEach(function(h, i){
    timers.push(setTimeout(function(){
      var a=dev(h.from), b=dev(h.to);
      var c=document.createElementNS('http://www.w3.org/2000/svg','circle');
      c.setAttribute('r',6); c.setAttribute('fill',col); c.setAttribute('stroke','#fff');
      world().appendChild(c);
      var t0=performance.now();
      function step(t){ var k=Math.min(1,(t-t0)/500); c.setAttribute('cx',a.x+(b.x-a.x)*k); c.setAttribute('cy',a.y+(b.y-a.y)*k); if(k<1){ requestAnimationFrame(step); } else { c.remove(); } }
      requestAnimationFrame(step);
      log(label+' hop'+(i+1)+': '+(a.name||a.id)+' → '+(b.name||b.id)+'  ['+(h.L.mode==='trunk'?'trunk v'+v+' ok':'access v'+v+' ok')+']');
    }, i*550));
  });
}
window.nlStop=function(){ timers.forEach(clearTimeout); timers=[]; log('⏹ остановлено'); };
window.nlSim=function(){
  nlStop(); el('nlLog').textContent='';
  var src=+el('simSrc').value, dst=+el('simDst').value, mode=el('simMode').value, v=el('simVlan').value||'1';
  var s=dev(src); if(!s){ log('нет источника'); return; }
  log('▶ '+mode+' VLAN '+v+' от '+(s.name||s.id));
  if(mode==='unicast'){
    var hops=path(src,dst,v);
    if(!hops){ log('❌ пути нет: VLAN '+v+' не пропущен на каком-то участке (проверьте trunk-списки / access-VLAN)'); return; }
    animate(hops,v,'📨');
    timers.push(setTimeout(function(){ log('✅ доставлено: '+(dev(dst).name||dst); }, hops.length*550+200));
  } else if(mode==='multicast'){
    var viewers=S.devices.filter(function(d){ return d.id!==src && String(d.vlan)===String(v) && (d.type==='pc'||d.type==='server'||d.type==='printer'); });
    if(!viewers.length){ log('❌ нет viewers с VLAN '+v); return; }
    viewers.forEach(function(d){ var h=path(src,d.id,v); if(h){ animate(h,v,'📺→'+(d.name||d.id)); } else { log('❌ '+(d.name||d.id)+': VLAN не доходит'); } });
  } else {
    var seen={}, q=[src], edges=[]; seen[src]=true; var storm=false;
    while(q.length){ var cur=q.shift();
      neighbors(cur,v).forEach(function(n){
        edges.push({from:cur,to:n.to,L:n.L});
        if(seen[n.to]){ storm=true; } else { seen[n.to]=true; q.push(n.to); }
      });
    }
    edges.forEach(function(e,i){ timers.push(setTimeout(function(){ animate([e],v,'🌊'); }, i*120)); });
    log(storm? '⚠️ ОБНАРУЖЕНА ПЕТЛЯ → broadcast-шторм! включите loopdetect/RSTP' : '🌊 flood дошёл до '+Object.keys(seen).length+' устройств');
  }
};
// ---- сохранение/экспорт ----
function pin(){ return localStorage.getItem('swhpin')||prompt('PIN:')||''; }
window.nlSave=function(){
  var name=prompt('Название схемы:', 'Схема ЛВС');
  if(!name) return;
  fetch('/api/schemes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin(), name:name, data:JSON.stringify(S)})})
  .then(function(r){return r.json();}).then(function(res){ alert(res.ok? 'Сохранено #'+res.id : 'Ошибка: '+(res.error||'')); });
};
window.nlList=function(){
  fetch('/api/schemes').then(function(r){return r.json();}).then(function(rows){
    if(!rows.length){ alert('Сохранённых схем нет'); return; }
    var pick=prompt('Открыть схему (ID):\n'+rows.map(function(r){return r.id+': '+r.name+' ('+r.updated_at+')';}).join('\n'), rows[0].id);
    if(!pick) return;
    fetch('/api/schemes/'+pick).then(function(r){return r.json();}).then(function(sc){
      if(sc.data){ S=JSON.parse(sc.data); sel=null; selLink=null; render(); log('📂 открыто: '+sc.name); }
    });
  });
};
window.nlExport=function(fmt){
  var clone=svg().cloneNode(true);
  clone.setAttribute('xmlns','http://www.w3.org/2000/svg');
  clone.setAttribute('width',1400); clone.setAttribute('height',900);
  var blob=new Blob([clone.outerHTML],{type:'image/svg+xml'});
  if(fmt==='svg'){ var a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='scheme.svg'; a.click(); return; }
  var img=new Image();
  img.onload=function(){ var c=document.createElement('canvas'); c.width=1400; c.height=900; var ctx=c.getContext('2d'); ctx.fillStyle='#fff'; ctx.fillRect(0,0,1400,900); ctx.drawImage(img,0,0); var a=document.createElement('a'); a.href=c.toDataURL('image/png'); a.download='scheme.png'; a.click(); };
  img.src=URL.createObjectURL(blob);
};
window.nlDemo=function(){
  S={nid:9,lid:9,devices:[
    {id:1,type:'core',x:400,y:60,name:'Ядро S6330',ip:'10.163.100.8',vlan:'',model:'S6330'},
    {id:2,type:'switch',x:250,y:200,name:'DES-3200 подъезд',ip:'10.163.202.88',vlan:'',model:'DES-3200-28'},
    {id:3,type:'camera',x:120,y:340,name:'Камера БР-6',ip:'10.135.1.232',vlan:'135',model:'BEWARD'},
    {id:4,type:'pc',x:330,y:340,name:'Абонент кв.12',ip:'10.163.5.12',vlan:'2050',model:''},
    {id:5,type:'olt',x:600,y:200,name:'OLT',ip:'10.163.206.8',vlan:'',model:'PON'},
    {id:6,type:'split',x:600,y:320,name:'Сплиттер 1:8',ip:'',vlan:'',model:''},
    {id:7,type:'onu',x:520,y:430,name:'ONU камера',ip:'',vlan:'135',model:'ONT'},
    {id:8,type:'camera',x:520,y:540,name:'Камера PON',ip:'10.135.2.10',vlan:'135',model:'BEWARD'}
  ],links:[
    {id:1,a:1,b:2,pa:'4',pb:'28',mode:'trunk',vlans:'135,1151,2050',media:'fiber'},
    {id:2,a:2,b:3,pa:'21',pb:'1',mode:'access',vlans:'135',media:'copper'},
    {id:3,a:2,b:4,pa:'12',pb:'1',mode:'access',vlans:'2050',media:'copper'},
    {id:4,a:1,b:5,pa:'6',pb:'1',mode:'trunk',vlans:'135,1151,2050',media:'fiber'},
    {id:5,a:5,b:6,pa:'pon1',pb:'in',mode:'trunk',vlans:'135,2050',media:'pon'},
    {id:6,a:6,b:7,pa:'3',pb:'pon',mode:'trunk',vlans:'135,2050',media:'pon'},
    {id:7,a:7,b:8,pa:'lan1',pb:'1',mode:'access',vlans:'135',media:'copper'}
  ]};
  sel=null; selLink=null; render(); log('📦 пример загружен: камера БР + PON. Выберите источник/приёмник и жмите ▶');
};
palette(); nlDemo();
})();
'''
open('static/netlab.js', 'w').write(NLJS)
FIXES.append('netlab.js'); print('  ok: static/netlab.js')

# 3) Штамп + проверка + запись
try:
    ast.parse(src)
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v21_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v21', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v21. Правок:', len(FIXES), '| бэкап: backups/swh_pre_v21_' + TS + '.py')
