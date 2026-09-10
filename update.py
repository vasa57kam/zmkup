import ast, os
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''

# 1) Кликабельный IP в карточке камеры + функции удаления/чистки
if 'openIp' not in ajs:
    ajs = ajs.replace("""<input class="camIp" value="'+(c.ip||'')+'"></div>'""",
"""<input class="camIp" value="'+(c.ip||'')+'"> <button class="btn btn-secondary" style="padding:2px 6px;" onclick="openIp('+c.id+')" title="Открыть веб-интерфейс камеры">🔗</button></div>'""", 1)
    ajs += '''
function openIp(id){
  var d=document.querySelector('[data-cam="'+id+'"]');
  var u=d && d.querySelector('.camIp').value;
  if(u){ window.open('http://'+u,'_blank'); } else { alert('IP не указан'); }
}
function delCamPlan(id){
  if(!confirm('Удалить камеру?')) return;
  fetch('/api/cameras/'+id,{method:'DELETE'}).then(function(){
    if(typeof renderCamPlan==='function'){ renderCamPlan(); }
    if(typeof loadCams==='function'){ loadCams(); }
  });
}
function cleanEmptyCams(){
  fetch('/api/cameras?order_id='+orderId).then(function(r){return r.json();}).then(function(rows){
    var empty=rows.filter(function(c){
      return !(c.model||'').trim() && !(c.ip||'').trim() && !(c.serial||'').trim() && !(c.login||'').trim() && !(c.rtsp||'').trim();
    });
    if(!empty.length){ alert('Пустых камер нет'); return; }
    if(!confirm('Удалить пустых камер: '+empty.length+'?')) return;
    Promise.all(empty.map(function(c){ return fetch('/api/cameras/'+c.id,{method:'DELETE'}); }))
      .then(function(){
        if(typeof renderCamPlan==='function'){ renderCamPlan(); }
        if(typeof loadCams==='function'){ loadCams(); }
      });
  });
}
'''
    open(ajs_path, 'w').write(ajs)
    print('ok: openIp + удаление камер')
else:
    print('openIp уже есть')

# 2) План камер: кликабельный IP + 🗑 у каждой карточки + кнопка чистки
rep("""      h+='<b>📹 '+(c.side==='old'?'СТАРНАЯ':'НОВАЯ')+' камера:</b> '+(c.model||'—')+' | IP/ID: '+(c.ip||'без IP')+' | логин: '+(c.login||'—');""",
"""      h+='<button class="btn btn-danger" style="padding:1px 6px;margin-right:.4rem;" onclick="delCamPlan('+c.id+')" title="Удалить камеру">🗑</button>';
      h+='<b>📹 '+(c.side==='old'?'СТАРНАЯ':'НОВАЯ')+' камера:</b> '+(c.model||'—')+' | IP/ID: '+(c.ip?'<a href="http://'+c.ip+'" target="_blank">'+c.ip+'</a>':'без IP')+' | логин: '+(c.login||'—');""",
    'план: IP-ссылка и 🗑')

rep("""    box.innerHTML=h;
  });
}
function loadSubscribers() {""",
"""    h='<button class="btn btn-secondary" style="margin-bottom:.5rem;" onclick="cleanEmptyCams()">🧹 Убрать пустые камеры</button>'+h;
    box.innerHTML=h;
  });
}
function loadSubscribers() {""", 'план: кнопка чистки пустых')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')