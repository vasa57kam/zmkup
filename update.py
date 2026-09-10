import ast, os
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) RTSP: кнопки «Открыть поток» и «Копировать» в карточке камеры
ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'openRtsp' not in ajs:
    ajs = ajs.replace("""placeholder="rtsp://admin:pass@ip:554/av0_0"></div>'""",
"""placeholder="rtsp://admin:pass@ip:554/av0_0"> '
   +'<button class="btn btn-secondary" style="margin-left:.4rem;" onclick="openRtsp('+c.id+')">🔗 Открыть поток</button> '
   +'<button class="btn btn-secondary" onclick="copyRtsp('+c.id+')">📋</button></div>'""", 1)
    ajs += '''
function openRtsp(id){
  var d=document.querySelector('[data-cam="'+id+'"]');
  var u=d && d.querySelector('.camRtsp').value;
  if(u){ window.open(u,'_blank'); } else { alert('RTSP не указан'); }
}
function copyRtsp(id){
  var d=document.querySelector('[data-cam="'+id+'"]');
  var u=d && d.querySelector('.camRtsp').value;
  if(u){ navigator.clipboard.writeText(u); alert('RTSP скопирован'); } else { alert('RTSP не указан'); }
}
function copyTxt(t){ navigator.clipboard.writeText(t); alert('Скопировано'); }
'''
    open(ajs_path, 'w').write(ajs)
    print('ok: RTSP кликабельный')
else:
    print('RTSP кнопки уже есть')

# 2) Планировщик: блок «План установки камер»
if 'id="camPlan"' not in src:
    rep('<h3>🗺️ Карта наряда: как было / как станет</h3>',
"""<h3 id="camPlanH" style="display:none;">📹 План установки камер</h3>
<div id="camPlan" style="background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;display:none;"></div>
<h3>🗺️ Карта наряда: как было / как станет</h3>""", 'блок кам-плана в планировщике')

    rep('loadSubscribers();\nloadLinks();',
"""loadSubscribers();
loadLinks();
renderCamPlan();""", 'вызов renderCamPlan')

    rep('function loadSubscribers() {',
"""function renderCamPlan(){
  fetch('/api/cameras?order_id='+orderId).then(function(r){return r.json();}).then(function(rows){
    var hEl=document.getElementById('camPlanH');
    var box=document.getElementById('camPlan');
    if(!box) return;
    if(!rows.length){ if(hEl){hEl.style.display='none';} box.style.display='none'; return; }
    if(hEl){hEl.style.display='';} box.style.display='';
    var h='';
    rows.forEach(function(c){
      h+='<div style="border:1px solid #ddd;border-radius:8px;padding:.7rem;margin:.4rem 0;">';
      h+='<b>📹 '+(c.side==='old'?'СТАРНАЯ':'НОВАЯ')+' камера:</b> '+(c.model||'—')+' | IP/ID: '+(c.ip||'без IP')+' | логин: '+(c.login||'—');
      h+='<br>📍 зона/надпись: '+(c.zone||'—')+' | серийник: '+(c.serial||'—');
      h+='<br>🔌 свитч: <b>'+(c.switch_name||'—')+'</b>'+(devLocSync(c.switch_name)?' 📍 '+devLocSync(c.switch_name):'')+', порт '+(c.switch_port||'—')+' | порт/VLAN: '+(c.port||'—')+'/'+(c.vlan||'—');
      if(c.rtsp){
        h+='<br>🎬 RTSP: <a href="'+c.rtsp+'" target="_blank">'+c.rtsp+'</a> <button class="btn btn-secondary" style="padding:1px 6px;" data-t="'+c.rtsp+'" onclick="copyTxt(this.dataset.t)">📋</button>';
      }
      if(c.notes){ h+='<br>📝 '+c.notes; }
      h+='</div>';
    });
    var nc=rows.filter(function(c){return c.side==='new';})[0]||rows[0];
    h+='<h3>🔔 НЕ ЗАБЫТЬ (камеры):</h3><ul style="margin-left:1.2rem;line-height:1.7;">'
      +'<li>Настроить новую камеру: логин/пароль, время, RTSP.</li>'
      +'<li>Переподключить в биллинге: порт '+(nc.port||'—')+' / VLAN '+(nc.vlan||'—')+'.</li>'
      +'<li>Проверить поток и архив записи ('+(nc.rtsp||'rtsp новой камеры')+').</li>'
      +'<li>Обновить карточку: номер БР, подъезд, надпись.</li>'
      +'</ul>';
    box.innerHTML=h;
  });
}
function loadSubscribers() {""", 'renderCamPlan в планировщике')

    # для типа «камера» прячем карту свитчей в планировщике
    rep('            applyNewMode(order);',
"""            applyNewMode(order);
            if((order.order_type||'')==='camera'){
              var om=document.getElementById('orderMap');
              if(om){ if(om.previousElementSibling){ om.previousElementSibling.style.display='none'; } om.style.display='none'; }
            }""", 'камера: скрыть карту свитчей')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')