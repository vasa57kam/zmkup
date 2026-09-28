import ast, os
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

import sqlite3
conn = sqlite3.connect('switch_replacements.db')
conn.execute('''CREATE TABLE IF NOT EXISTS kb_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, category TEXT, tags TEXT, body TEXT, schema TEXT, created_at TEXT)''')
conn.commit()
conn.close()
print('ok: таблица kb_articles')

# 1) Эндпоинты базы знаний
if "'/api/kb'" not in src:
    EP = '''
@app.route('/kb')
def kb_page():
    return render_template_string(KB_HTML)

@app.route('/api/kb', methods=['GET', 'POST'])
def kb_api():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('SELECT id, title, category, tags, body, created_at FROM kb_articles ORDER BY id DESC').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        conn.close()
        return jsonify({'error': 'pin'}), 403
    c = conn.cursor()
    c.execute('INSERT INTO kb_articles (title, category, tags, body, schema, created_at) VALUES (?,?,?,?,?,?)',
              (d.get('title', ''), d.get('category', 'Прочее'), d.get('tags', ''), d.get('body', ''), '',
               datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    i = c.lastrowid
    conn.close()
    return jsonify({'ok': True, 'id': i})

@app.route('/api/kb/<int:aid>', methods=['GET', 'PUT', 'DELETE'])
def kb_item(aid):
    conn = get_db()
    if request.method == 'GET':
        r = conn.execute('SELECT * FROM kb_articles WHERE id=?', (aid,)).fetchone()
        conn.close()
        if not r:
            return jsonify({'error': 'nf'}), 404
        return jsonify(dict(r))
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        conn.close()
        return jsonify({'error': 'pin'}), 403
    if request.method == 'DELETE':
        conn.execute('DELETE FROM kb_articles WHERE id=?', (aid,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    sets = []
    vals = []
    for f in ('title', 'category', 'tags', 'body', 'schema'):
        if f in d:
            sets.append(f + '=?')
            vals.append(d[f])
    if sets:
        vals.append(aid)
        conn.execute('UPDATE kb_articles SET ' + ','.join(sets) + ' WHERE id=?', vals)
        conn.commit()
    conn.close()
    return jsonify({'ok': True})


KB_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>📖 База знаний</title>
<style>body{font-family:Arial;font-size:16px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:14px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
.big{font-size:22px;font-weight:600;}
.btn{padding:10px 16px;border:none;border-radius:8px;color:#fff;font-size:15px;cursor:pointer;margin:3px;}
input,select,textarea{padding:8px;border:1px solid #ccc;border-radius:6px;font-size:15px;margin:3px;}
.badge{background:#1565c0;color:#fff;border-radius:10px;padding:2px 10px;font-size:13px;}
@media print{.noprint{display:none !important;}}
</style></head>
<body>
<div class="card big noprint">📖 База знаний (схемы, инструкции, пояснения)</div>
<div class="card noprint">
<input id="q" placeholder="Поиск: заголовок, теги, текст (напр. RS485, домофон, камера)" oninput="renderList()" style="width:55%;">
<select id="cat" onchange="renderList()">
<option value="">Все категории</option><option>Домофон</option><option>Камеры</option><option>Свитчи</option><option>VLAN</option><option>Питание</option><option>Прочее</option>
</select>
<button class="btn" style="background:#27ae60;" onclick="showCreate()">➕ Новая статья</button>
</div>
<div id="content"></div>
<script src="/static/common.js?v=3"></script>
<script src="/static/kb.js?v=1"></script>
</body></html>"""
'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + EP + src[idx:]
    print('ok: эндпоинты и страница /kb')

# 2) JS базы знаний + редактор схем
KBJS = r'''var CUR=null;
function qs(){ return new URLSearchParams(location.search); }
function esc(s){ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function pin(){ return localStorage.getItem('swhpin')||prompt('PIN:')||''; }
function boot(){ if(qs().get('id')){ renderArticle(parseInt(qs().get('id'))); } else { renderList(); } }
function renderList(){
  var q=(document.getElementById('q').value||'').toLowerCase();
  var cat=document.getElementById('cat').value;
  fetch('/api/kb').then(function(r){return r.json();}).then(function(rows){
    var f=rows.filter(function(a){
      if(cat && a.category!==cat) return false;
      if(!q) return true;
      return (a.title||'').toLowerCase().indexOf(q)>=0 || (a.tags||'').toLowerCase().indexOf(q)>=0 || (a.body||'').toLowerCase().indexOf(q)>=0;
    });
    document.getElementById('content').innerHTML=f.map(function(a){
      return '<div class="card" style="cursor:pointer;" onclick="location.href=\'/kb?id='+a.id+'\'">'
        +'<div class="big">'+esc(a.title)+' <span class="badge">'+esc(a.category||'Прочее')+'</span></div>'
        +'<div><small>Теги: '+(a.tags||'—')+' | '+(a.created_at||'')+'</small></div>'
        +'<div style="margin-top:6px;">'+esc((a.body||'').slice(0,220)).replace(/\n/g,' ')+'…</div></div>';
    }).join('')||'<div class="card">Ничего не найдено. Создайте первую статью кнопкой «➕ Новая статья».</div>';
  });
}
function showCreate(){ editForm(null); }
function editForm(a){
  document.getElementById('content').innerHTML='<div class="card noprint"><b>'+(a?'✏️ Редактирование':'➕ Новая статья')+'</b><br>'
   +'Заголовок: <input id="fTitle" style="width:60%;" value="'+(a?esc(a.title):'')+'"><br>'
   +'Категория: <select id="fCat">'+['Домофон','Камеры','Свитчи','VLAN','Питание','Прочее'].map(function(x){return '<option'+(a&&a.category===x?' selected':'')+'>'+x+'</option>';}).join('')+'</select>'
   +' Теги: <input id="fTags" style="width:40%;" value="'+(a?esc(a.tags||''):'')+'" placeholder="RS485, Domovoy, Boxer..."><br>'
   +'Описание (что куда подключено, нюансы, версии):<textarea id="fBody" style="width:100%;height:220px;">'+(a?esc(a.body):'')+'</textarea><br>'
   +'<button class="btn" style="background:#27ae60;" onclick="saveArticle('+(a?a.id:'null')+')">💾 Сохранить</button> '
   +'<button class="btn" style="background:#7f8c8d;" onclick="boot()">Отмена</button></div>';
}
function saveArticle(id){
  var b={title:document.getElementById('fTitle').value, category:document.getElementById('fCat').value,
    tags:document.getElementById('fTags').value, body:document.getElementById('fBody').value, pin:pin()};
  fetch(id? '/api/kb/'+id : '/api/kb',{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)})
  .then(function(r){return r.json();}).then(function(res){
    if(res.id){ location.href='/kb?id='+res.id; }
    else if(res.ok){ location.href='/kb?id='+id; }
    else { alert('Ошибка: '+(res.error||'')); }
  });
}
function renderArticle(id){
  CUR=id;
  fetch('/api/kb/'+id).then(function(r){return r.json();}).then(function(a){
    if(a.error){ alert('Статья не найдена'); location.href='/kb'; return; }
    window.ART=a;
    document.getElementById('content').innerHTML='<div class="card"><div class="big">'+esc(a.title)+' <span class="badge">'+esc(a.category||'Прочее')+'</span></div>'
      +'<div><small>Теги: '+(a.tags||'—')+' | '+(a.created_at||'')+'</small></div>'
      +'<pre style="white-space:pre-wrap;font-family:inherit;margin-top:8px;">'+esc(a.body)+'</pre>'
      +'<div id="imgs"></div><div id="schemaBox"></div>'
      +'<div class="noprint" style="margin-top:8px;">'
      +'<button class="btn" style="background:#3498db;" onclick="editForm(window.ART)">✏️ Редактировать</button> '
      +'<button class="btn" style="background:#8e44ad;" onclick="toggleEditor()">🎨 Схема: рисовать/править</button> '
      +'<button class="btn" style="background:#27ae60;" onclick="window.print()">🖨️ Печать</button> '
      +'<button class="btn" style="background:#e74c3c;" onclick="delArticle()">🗑 Удалить</button> '
      +'<button class="btn" style="background:#7f8c8d;" onclick="location.href=\'/kb\'">← К списку</button></div></div>';
    loadImgs();
    renderSchemaView();
  });
}
function delArticle(){
  if(!confirm('Удалить статью?')) return;
  fetch('/api/kb/'+CUR,{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin()})})
  .then(function(){ location.href='/kb'; });
}
function loadImgs(){
  fetch('/api/attachments?entity_type=kb&entity_id='+CUR).then(function(r){return r.json();}).then(function(rows){
    document.getElementById('imgs').innerHTML='<b>📎 Картинки и файлы:</b><br>'
      +rows.map(function(x){
        return '<span style="display:inline-block;margin:6px;text-align:center;"><a href="/uploads/'+x.filename+'" target="_blank"><img src="/uploads/'+x.filename+'" style="width:160px;height:115px;object-fit:cover;border-radius:6px;"></a><br><small>'+esc(x.original_name||'')+'</small> <button class="noprint" onclick="delKbImg('+x.id+')">🗑</button></span>';
      }).join('')
      +'<div class="noprint"><input type="file" multiple onchange="upKb(this)"></div>';
  });
}
function delKbImg(id){ fetch('/api/attachments/'+id,{method:'DELETE'}).then(loadImgs); }
function upKb(inp){
  var files=inp.files; var done=0;
  if(!files.length) return;
  for(var i=0;i<files.length;i++){
    var fd=new FormData();
    fd.append('file',files[i]); fd.append('entity_type','kb'); fd.append('entity_id',CUR); fd.append('description','');
    fetch('/api/attachments',{method:'POST',body:fd}).then(function(){ done++; if(done>=files.length){ loadImgs(); } });
  }
  inp.value='';
}
var ED={on:false,data:{blocks:[],links:[]},sel:null,linkFrom:null,nid:1,drag:null};
function parseSchema(){ try{ return JSON.parse(window.ART.schema||'null')||{blocks:[],links:[]}; }catch(e){ return {blocks:[],links:[]}; } }
function renderSchemaView(){
  var box=document.getElementById('schemaBox');
  var d=parseSchema();
  box.innerHTML=d.blocks.length? '<b>🎨 Схема подключения:</b>'+svgMarkup(d,false) : '';
}
function svgMarkup(d,edit){
  var s='<svg id="ksvg" width="1000" height="620" style="background:#fff;border:1px solid #ccc;max-width:100%;">';
  d.links.forEach(function(L){
    var a=null,b=null;
    d.blocks.forEach(function(x){ if(x.id===L[0])a=x; if(x.id===L[1])b=x; });
    if(a&&b){ s+='<line x1="'+(a.x+a.w/2)+'" y1="'+(a.y+a.h/2)+'" x2="'+(b.x+b.w/2)+'" y2="'+(b.y+b.h/2)+'" stroke="#333" stroke-width="2"/>'; }
  });
  d.blocks.forEach(function(b){
    s+='<g '+(edit?'onmousedown="blockDown(evt,'+b.id+')" style="cursor:move;"':'')+'>'
      +'<rect x="'+b.x+'" y="'+b.y+'" width="'+b.w+'" height="'+b.h+'" fill="'+(edit&&b.id===ED.sel?'#ffe082':'#e3f2fd')+'" stroke="#1565c0" stroke-width="2" rx="6"/>'
      +'<text x="'+(b.x+b.w/2)+'" y="'+(b.y+b.h/2+5)+'" text-anchor="middle" font-size="14">'+esc(b.label)+'</text></g>';
  });
  return s+'</svg>';
}
function toggleEditor(){
  ED.on=!ED.on;
  var box=document.getElementById('schemaBox');
  if(!ED.on){ renderSchemaView(); return; }
  ED.data=parseSchema();
  ED.nid=ED.data.blocks.reduce(function(m,b){return Math.max(m,b.id);},0)+1;
  box.innerHTML='<b>🎨 Редактор схемы:</b> <button class="btn noprint" style="background:#3498db;" onclick="addBlock()">➕ Блок</button> '
   +'<button class="btn noprint" style="background:#9c27b0;" onclick="startLink()">🔗 Связать</button> '
   +'<button class="btn noprint" style="background:#e74c3c;" onclick="delSel()">🗑 Удалить выбранное</button> '
   +'<button class="btn noprint" style="background:#27ae60;" onclick="saveSchema()">💾 Сохранить схему</button> '
   +'<span id="edHint">Клик по блоку — выбрать; перетаскивание — двигать; «Связать» — клик по двум блокам.</span><div id="edwrap"></div>';
  drawEd();
}
function drawEd(){ document.getElementById('edwrap').innerHTML=svgMarkup(ED.data,true); }
function addBlock(){
  var l=prompt('Надпись блока (напр. Domovoy RS485 V1.2):');
  if(!l) return;
  ED.data.blocks.push({id:ED.nid++,x:60+Math.random()*500,y:40+Math.random()*300,w:170,h:60,label:l});
  drawEd();
}
function svgPoint(svg,e){ var r=svg.getBoundingClientRect(); return {x:e.clientX-r.left,y:e.clientY-r.top}; }
function blockDown(e,id){
  e.stopPropagation();
  if(ED.linkFrom && ED.linkFrom!==id){ ED.data.links.push([ED.linkFrom,id]); ED.linkFrom=null; drawEd(); return; }
  ED.sel=id;
  var b=null;
  ED.data.blocks.forEach(function(x){ if(x.id===id)b=x; });
  var pt=svgPoint(document.getElementById('ksvg'),e);
  ED.drag={dx:pt.x-b.x,dy:pt.y-b.y};
  drawEd();
}
document.addEventListener('mousemove',function(e){
  if(!ED.on||!ED.drag||!ED.sel) return;
  var svg=document.getElementById('ksvg');
  if(!svg) return;
  var pt=svgPoint(svg,e); var b=null;
  ED.data.blocks.forEach(function(x){ if(x.id===ED.sel)b=x; });
  if(b){ b.x=Math.max(0,Math.min(990-b.w,pt.x-ED.dx)); b.y=Math.max(0,Math.min(610-b.h,pt.y-ED.dy)); drawEd(); }
});
document.addEventListener('mouseup',function(){ ED.drag=null; });
function startLink(){ ED.linkFrom=ED.sel; document.getElementById('edHint').textContent=ED.sel? 'Теперь кликните ВТОРОЙ блок для связи.' : 'Сначала кликните блок, потом «Связать».'; }
function delSel(){
  if(!ED.sel) return;
  ED.data.blocks=ED.data.blocks.filter(function(b){return b.id!==ED.sel;});
  ED.data.links=ED.data.links.filter(function(L){return L[0]!==ED.sel&&L[1]!==ED.sel;});
  ED.sel=null; drawEd();
}
function saveSchema(){
  fetch('/api/kb/'+CUR,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({schema:JSON.stringify(ED.data),pin:pin()})})
  .then(function(r){return r.json();}).then(function(res){
    alert(res.ok? 'Схема сохранена':'Ошибка: '+(res.error||''));
    ED.on=false; renderSchemaView();
  });
}
window.addEventListener('DOMContentLoaded',boot);
'''
open('static/kb.js', 'w').write(KBJS)
print('ok: static/kb.js')

# 3) Ссылка в меню
KB_LINK = '<a href="/kb" class="nav-link">📖 База знаний</a>'
if KB_LINK not in src:
    rep('<a href="/vlans" class="nav-link">🗂 VLANы</a>',
        '<a href="/vlans" class="nav-link">🗂 VLANы</a>\n            ' + KB_LINK,
        'ссылка База знаний')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')