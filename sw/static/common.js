window.devArr=[];
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

function camCard(c){
  var side=c.side==='old'?'СТАРНАЯ':'НОВАЯ';
  return '<div style="border:1px solid #ddd;border-radius:8px;padding:.8rem;margin:.5rem 0;" data-cam="'+c.id+'">'
   +'<b>📹 '+side+' камера</b> '
   +'<button class="btn btn-danger" style="padding:2px 8px;" onclick="delCam('+c.id+')">🗑</button>'
   +'<div class="form-row">'
   +'<div class="form-group"><label>Модель:</label><input class="camModel" value="'+(c.model||'')+'" placeholder="Beward BR-2.4 и т.п."></div>'
   +'<div class="form-group"><label>Серийник:</label><input class="camSerial" value="'+(c.serial||'')+'"></div>'
   +'<div class="form-group"><label>IP / ID:</label><input class="camIp" value="'+(c.ip||'')+'"> <button class="btn btn-secondary" style="padding:2px 6px;" onclick="openIp('+c.id+')" title="Открыть веб-интерфейс камеры">🔗</button></div>'
   +'</div>'
   +'<div class="form-row">'
   +'<div class="form-group"><label>MAC:</label><input class="camMac" value="'+(c.mac||'')+'"></div>'
   +'<div class="form-group"><label>Зона / надпись:</label><input class="camZone" value="'+(c.zone||'')+'" placeholder="безопасный регион, надпись..."></div>'
   +'</div>'
   +'<div class="form-row">'
   +'<div class="form-group"><label>Логин:</label><input class="camLogin" value="'+(c.login||'')+'" placeholder="br-291095"></div>'
   +'<div class="form-group"><label>Пароль:</label><input class="camPass" value="'+(c.password||'')+'"></div>'
   +'<div class="form-group"><label>Порт / VLAN:</label><input class="camPort" value="'+(c.port||'')+'" placeholder="21"> / <input class="camVlan" value="'+(c.vlan||'')+'" placeholder="135"></div>'
   +'</div>'
   +'<div class="form-row">'
   +'<div class="form-group"><label>Свитч (где стоит):</label><select class="camSwitch"></select></div>'
   +'<div class="form-group"><label>Порт свитча:</label><input class="camSwitchPort" style="width:90px;" value="'+(c.switch_port||'')+'"></div>'
   +'</div>'
   +'<div class="form-group"><label>RTSP-поток:</label><input class="camRtsp" value="'+(c.rtsp||'')+'" placeholder="rtsp://admin:pass@ip:554/av0_0"> '
   +'<button class="btn btn-secondary" style="margin-left:.4rem;" onclick="openRtsp('+c.id+')">🔗 Открыть поток</button> '
   +'<button class="btn btn-secondary" onclick="copyRtsp('+c.id+')">📋</button></div>'
   +'<div class="form-group"><label>Примечания:</label><input class="camNotes" value="'+(c.notes||'')+'"></div>'
   +'<div class="form-group"><label>Конфиг (экспорт/импорт):</label><textarea class="camCfg" style="width:100%;height:90px;font-family:monospace;">'+(c.config_text||'')+'</textarea></div>'
   +'<button class="btn btn-primary" onclick="saveCam('+c.id+')">💾 Сохранить</button> '
   +'<button class="btn btn-secondary" onclick="exportCam('+c.id+')">📤 Экспорт конфига</button> '
   +'<button class="btn btn-secondary" onclick="importCam('+c.id+')">📥 Импорт конфига</button> '
   +'<button class="btn btn-secondary" onclick="camFromShot('+c.id+')">📸 Из скриншота</button>'
   +'<div class="form-group" style="margin-top:.5rem;"><label>Файлы камеры (конфиг, бэкап, фото шильдика):</label>'
   +'<div id="camFiles_'+c.id+'"></div>'
   +'<input type="file" onchange="uploadAttachment(\'camera\','+c.id+',\'camFiles_'+c.id+'\',this)"></div>'
   +'</div>';
}
function loadCams(){
  var box=document.getElementById('camsBox');
  if(!box) return;
  fetch('/api/cameras?order_id='+orderId).then(function(r){return r.json();}).then(function(rows){
    box.innerHTML=rows.map(camCard).join('')||'<small>Камер в наряде пока нет.</small>';
    rows.forEach(function(r){
      loadAttachments('camera', r.id, 'camFiles_'+r.id);
      var sel=document.querySelector('[data-cam="'+r.id+'"] .camSwitch');
      if(sel){
        devList().then(function(ds){
          var html='<option value="">— выберите свитч —</option>'+ds.map(function(d){
            return '<option value="'+d.name+'">'+d.name+' · '+(d.ip_address||'')+' · 📍 '+(d.location||'—')+'</option>';
          }).join('');
          var ex=r.switch_name && !ds.some(function(d){ return d.name===r.switch_name; });
          if(ex){ html+='<option value="'+r.switch_name+'">'+r.switch_name+' (текущий)</option>'; }
          sel.innerHTML=html;
          sel.value=r.switch_name||'';
        });
      }
    });
  });
}
function addCam(side){
  fetch('/api/cameras',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({order_id:orderId, side:side})}).then(loadCams);
}
function saveCam(id){
  var d=document.querySelector('[data-cam="'+id+'"]');
  var body={model:d.querySelector('.camModel').value, serial:d.querySelector('.camSerial').value,
    ip:d.querySelector('.camIp').value, mac:d.querySelector('.camMac').value,
    zone:d.querySelector('.camZone').value, notes:d.querySelector('.camNotes').value,
    login:d.querySelector('.camLogin').value, password:d.querySelector('.camPass').value,
    rtsp:d.querySelector('.camRtsp').value, vlan:d.querySelector('.camVlan').value,
    switch_name:(d.querySelector('.camSwitch')||{}).value||'', switch_port:d.querySelector('.camSwitchPort').value,
    port:d.querySelector('.camPort').value,
    config_text:d.querySelector('.camCfg').value};
  fetch('/api/cameras/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(){alert('Сохранено');});
}
function delCam(id){
  if(!confirm('Удалить камеру?')) return;
  fetch('/api/cameras/'+id,{method:'DELETE'}).then(loadCams);
}
function exportCam(id){
  fetch('/api/cameras/'+id).then(function(r){return r.json();}).then(function(c){
    var NL=String.fromCharCode(10);
    var txt='КАМЕРА '+(c.side||'')+NL+'Модель: '+(c.model||'')+NL+'Серийник: '+(c.serial||'')+NL+'IP/ID: '+(c.ip||'')+NL+'MAC: '+(c.mac||'')+NL+'Зона: '+(c.zone||'')+NL+'Примечания: '+(c.notes||'')+NL+NL+'КОНФИГ:'+NL+(c.config_text||'');
    var b=new Blob([txt],{type:'text/plain'});
    var a=document.createElement('a');
    a.href=URL.createObjectURL(b);
    a.download='camera_'+(c.model||'cam')+'_'+(c.serial||id)+'.txt';
    a.click();
  });
}
function importCam(id){
  var inp=document.createElement('input');
  inp.type='file';
  inp.onchange=function(){
    var f=inp.files[0];
    if(!f) return;
    var r=new FileReader();
    r.onload=function(){
      var d=document.querySelector('[data-cam="'+id+'"]');
      d.querySelector('.camCfg').value=r.result;
      alert('Конфиг загружен в поле. Не забудьте 💾 Сохранить');
    };
    r.readAsText(f);
  };
  inp.click();
}

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

function camFromShot(id){
  var inp=document.createElement('input');
  inp.type='file'; inp.accept='image/*';
  inp.onchange=function(){
    var f=inp.files[0];
    if(!f) return;
    var fd=new FormData();
    fd.append('file', f);
    fd.append('pin', localStorage.getItem('swhpin')||prompt('PIN:')||'');
    alert('Распознаю скриншот (до минуты)...');
    fetch('/api/vision',{method:'POST', body:fd}).then(function(r){return r.json();}).then(function(res){
      if(!res.data){ alert('Ошибка: '+(res.error||'неизвестно')+(res.raw?' | '+res.raw:'')); return; }
      var d=res.data;
      var c=document.querySelector('[data-cam="'+id+'"]');
      if(!c) return;
      function set(cls, v){ if(v){ var el=c.querySelector(cls); if(el){ el.value=v; } } }
      set('.camLogin', d.login); set('.camPass', d.password); set('.camIp', d.ip);
      set('.camPort', d.port); set('.camVlan', d.vlan); set('.camMac', d.mac);
      set('.camRtsp', d.rtsp); set('.camModel', d.model); set('.camSerial', d.serial);
      set('.camZone', d.address); set('.camNotes', d.name);
      alert('Поля заполнены! Проверьте и нажмите 💾 Сохранить');
    }).catch(function(e){ alert('Ошибка: '+e.message); });
  };
  inp.click();
}
function fetchFdb(){
  var el=document.getElementById('fdbIp');
  var body={order_id:parseInt(el.dataset.order), ip:el.value,
    community:document.getElementById('fdbCom').value,
    side:document.getElementById('fdbSide').value};
  document.getElementById('fdbMsg').textContent='Снимаю FDB...';
  fetch('/api/fdb_fetch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  .then(function(r){return r.json();}).then(function(res){
    document.getElementById('fdbMsg').textContent=res.ok? ('Готово: '+res.count+' записей') : ('Ошибка: '+res.error);
    if(res.ok){ setTimeout(function(){ location.reload(); }, 1200); }
  });
}
document.addEventListener('DOMContentLoaded', function(){
  if(location.pathname.indexOf('/fdb/')===0){
    var c=document.querySelector('.container');
    if(c){
      var d=document.createElement('div');
      d.style.cssText='background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;';
      d.innerHTML='<b>🧲 Снять FDB со свитча (SNMP)</b><br>IP: <input id="fdbIp" style="width:140px;"> Community: <input id="fdbCom" value="public" style="width:100px;"> Сторона: <select id="fdbSide"><option value="old">ДО</option><option value="new">ПОСЛЕ</option></select> <button class="btn btn-primary" onclick="fetchFdb()">Снять</button> <span id="fdbMsg"></span>';
      c.insertBefore(d, c.firstChild);
      var m=location.pathname.match(/\/fdb\/(\d+)/);
      if(m){
        document.getElementById('fdbIp').dataset.order=m[1];
        fetch('/api/orders/'+m[1]).then(function(r){return r.json();}).then(function(o){
          document.getElementById('fdbIp').value=o.old_switch_ip||'';
        });
      }
    }
  }
});

function openDevTools(s){
  if(!s){ alert('Устройство не указано'); return; }
  var ip=(s.match(/(\d{1,3}\.){3}\d{1,3}/)||[null])[0];
  if(!ip && window.devArr){
    var d=devArr.find(function(x){ return x.name===s; });
    if(d){ ip=d.ip_address; }
  }
  if(!ip){ alert('Не найден IP устройства: '+s); return; }
  sessionStorage.setItem('toolz_tgt', ip);
  sessionStorage.setItem('toolz_tool', 'ssh');
  location.href='/tools';
}
