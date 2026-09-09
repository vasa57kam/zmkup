import ast, os
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Кнопки наряда статически в шаблоне (больше никакой JS-инъекции)
if 'id="closeBtn"' not in src:
    rep('<div id="orderDetails"></div>',
"""<div class="header-actions" style="margin-bottom:1rem;">
    <button id="closeBtn" class="btn btn-success" onclick="toggleOrderStatus()">✅ Закрыть наряд</button>
    <a class="btn btn-secondary" href="/api/report/{{ order_id }}" target="_blank">📄 Отчёт</a>
    <a class="btn btn-secondary" href="/passport/{{ order_id }}" target="_blank">🖨️ Паспорт</a>
    <a href="/planner/{{ order_id }}" class="btn btn-primary">🗺️ Планировщик</a>
    <a href="/fdb/{{ order_id }}" class="btn btn-success">📊 FDB</a>
</div>
<div id="orderDetails"></div>""", 'кнопки наряда в шаблоне')
else:
    print('  кнопки наряда уже есть')

# 2) Функции наряда и линий — в common.js (глобально, вне if-блоков)
ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
add_js = '''
function toggleOrderStatus(){
  var ns=(window.orderStatus==='closed')?'created':'closed';
  if(!confirm(ns==='closed'?'Закрыть наряд?':'Открыть наряд снова?')) return;
  fetch('/api/orders/'+orderId,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:ns})})
    .then(function(){ location.reload(); });
}
function refreshOrderHeader(){
  fetch('/api/orders/'+orderId).then(function(r){return r.json();}).then(function(o){
    window.orderStatus=o.status||'created';
    var h=document.querySelector('.page-header h1');
    if(h){ h.textContent='📋 Наряд №'+(o.order_number||orderId)+(window.orderStatus==='closed'?' 🔒 закрыт':''); }
    var b=document.getElementById('closeBtn');
    if(!b) return;
    if(window.orderStatus==='closed'){ b.textContent='↩️ Открыть снова'; b.className='btn btn-secondary'; }
    else { b.textContent='✅ Закрыть наряд'; b.className='btn btn-success'; }
  });
}
function updLink(id, field, val){
  var body={};
  body[field]=(field==='upstream_device')? val : (parseInt(val)||0);
  fetch('/api/links/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
}
function delLink(id){
  if(!confirm('Удалить линию?')) return;
  fetch('/api/links/'+id,{method:'DELETE'}).then(function(){ location.reload(); });
}
function addLinkToOrder(type){
  var body=(type==='uplink')
    ? {old_port:1, upstream_device:'', upstream_port:1, link_type:'uplink'}
    : {old_port:1, new_port:1, upstream_device:'', upstream_port:1, link_type:'downlink'};
  fetch('/api/links/'+orderId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
    .then(function(){ location.reload(); });
}
'''
if 'function toggleOrderStatus' not in ajs:
    open(ajs_path, 'w').write(ajs + add_js)
    print('ok: common.js + функции наряда/линий')
else:
    print('common.js уже содержит функции')

# 3) Вызов обновления шапки на странице наряда
if 'refreshOrderHeader();' not in src:
    rep('loadSteps();', 'loadSteps();\nrefreshOrderHeader();', 'вызов refreshOrderHeader')

# 4) linkDeletes с try/finally (замечание нейронки — реально полезно)
rep("""            if(window.linkDeletes && window.linkDeletes.length){
              for(const id of window.linkDeletes){
                await fetch('/api/links/'+id,{method:'DELETE'});
              }
              window.linkDeletes=[];
            }""",
"""            if(window.linkDeletes && window.linkDeletes.length){
              try{
                for(const id of window.linkDeletes){
                  await fetch('/api/links/'+id,{method:'DELETE'});
                }
              } finally { window.linkDeletes=[]; }
            }""", 'linkDeletes try/finally')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')