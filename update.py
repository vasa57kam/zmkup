import ast, os
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Общий JS в отдельный файл (неубиваемый)
common = r'''window.devArr=[];
function devList(){
  if(!window.devCache){
    window.devCache=fetch('/api/network-map').then(function(r){return r.json();}).then(function(ds){ window.devArr=ds; return ds; });
  }
  return window.devCache;
}
function devLocSync(s){
  if(!s||!window.devArr){ return ''; }
  for(var i=0;i<window.devArr.length;i++){
    var d=window.devArr[i];
    if(d.name && s.indexOf(d.name)>=0){ return d.location||''; }
    if(d.ip_address && s.indexOf(d.ip_address)>=0){ return d.location||''; }
  }
  return '';
}
function uploadAttachment(entityType, entityId, boxId, input){
  var f=input.files[0];
  if(!f) return;
  var fd=new FormData();
  fd.append('file', f);
  fd.append('entity_type', entityType);
  fd.append('entity_id', entityId);
  fd.append('description', '');
  fetch('/api/attachments',{method:'POST', body:fd})
    .then(function(){ input.value=''; return loadAttachments(entityType, entityId, boxId); });
}
function loadAttachments(type, id, boxId){
  return fetch('/api/attachments?entity_type='+type+'&entity_id='+id)
    .then(function(r){ return r.json(); })
    .then(function(rows){
      var box=document.getElementById(boxId);
      if(!box) return;
      box.innerHTML='';
      rows.forEach(function(a){
        var d=document.createElement('div');
        d.style.cssText='display:inline-block;margin:.4rem;text-align:center;';
        d.innerHTML='<a href="/uploads/'+a.filename+'" target="_blank"><img src="/uploads/'+a.filename+'" style="width:120px;height:90px;object-fit:cover;border-radius:6px;"></a><br><small>'+(a.original_name||'')+'</small> <button onclick="delAtt('+a.id+',\''+type+'\','+id+',\''+boxId+'\')">🗑</button>';
        box.appendChild(d);
      });
    });
}
function delAtt(id, type, ent, box){
  if(!confirm('Удалить фото?')) return;
  fetch('/api/attachments/'+id,{method:'DELETE'}).then(function(){ loadAttachments(type, ent, box); });
}
function openHelp(){
  var m=document.getElementById('helpModal');
  if(!m) return;
  m.style.display='block';
  fetch('/api/notes/global_help').then(function(r){return r.json();}).then(function(res){
    document.getElementById('helpArea').value=res.content||'';
  });
}
function closeHelp(){
  var m=document.getElementById('helpModal');
  if(m){ m.style.display='none'; }
}
function saveHelp(){
  var t=document.getElementById('helpArea').value;
  fetch('/api/notes/global_help',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:t})}).then(closeHelp);
}
if(document.readyState!=='loading'){ devList(); }
else { document.addEventListener('DOMContentLoaded', devList); }
'''
os.makedirs('static', exist_ok=True)
open('static/common.js', 'w').write(common)
print('ok: static/common.js записан')

# 2) Вырезаем мёртвый inline-скрипт из базы
i = src.find('async function loadAttachments')
if i > 0:
    k = src.rfind('<script>', 0, i)
    j = src.find('</script>', i)
    if k > 0 and j > i:
        src = src[:k] + src[j+len('</script>'):]
        print('ok: мёртвый inline-скрипт удалён из базы')
else:
    print('inline-скрипт уже удалён')

# 3) Подключаем common.js ДО скриптов страниц
if '<script src="/static/common.js' not in src:
    rep('{% block scripts %}{% endblock %}',
        '<script src="/static/common.js?v=2"></script>\n    {% block scripts %}{% endblock %}',
        'common.js подключён в базе')

# 4) Кнопки удаления строк uplink/downlink в форме
rep('''        <input type="number" placeholder="Порт устр." class="uplink-upstream-port">
    `;''',
'''        <input type="number" placeholder="Порт устр." class="uplink-upstream-port">
        <button type="button" class="btn btn-danger" style="padding:2px 8px;" onclick="rmRow(this)">🗑</button>
    `;''', '🗑 в строке uplink')

rep('''        <input type="number" placeholder="Порт (нов)" class="dl-new-port">
    `;''',
'''        <input type="number" placeholder="Порт (нов)" class="dl-new-port">
        <button type="button" class="btn btn-danger" style="padding:2px 8px;" onclick="rmRow(this)">🗑</button>
    `;''', '🗑 в строке downlink')

if 'function rmRow' not in src:
    rep('function fillDevSelect(sel, pre){',
"""function rmRow(btn){
  var row=btn.closest('.uplink-field');
  if(!row) return;
  if(row.dataset.linkId){
    window.linkDeletes=window.linkDeletes||[];
    window.linkDeletes.push(row.dataset.linkId);
  }
  row.remove();
}
function fillDevSelect(sel, pre){""", 'rmRow')

rep('editingId=id;', 'editingId=id; window.linkDeletes=[];', 'сброс linkDeletes')

rep("""            closeModal();
            loadOrders();""",
"""            if(window.linkDeletes && window.linkDeletes.length){
              for(const id of window.linkDeletes){
                await fetch('/api/links/'+id,{method:'DELETE'});
              }
              window.linkDeletes=[];
            }
            closeModal();
            loadOrders();""", 'удаление линий при сохранении')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')