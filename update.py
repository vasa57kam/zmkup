import os
js = r'''var jobTimer=null;
var localLines=[];
function logLine(t){ localLines.push(t); renderLog(window.jobLines||[]); }
function renderLog(jobLines){
  var el=document.getElementById('liveLog');
  if(!el){ return; }
  window.jobLines=jobLines||[];
  var all=localLines.concat(window.jobLines);
  el.textContent=all.join(String.fromCharCode(10));
  el.scrollTop=el.scrollHeight;
}
function getPin(){
  var p=document.getElementById('adminPin').value;
  if(p){ localStorage.setItem('swhpin',p); }
  else { p=localStorage.getItem('swhpin')||''; }
  return p;
}
function aiStatus(t){
  var el=document.getElementById('aiStatus');
  if(el){ el.textContent=t; }
}
function prog(on){
  var p=document.getElementById('prog');
  if(p){ p.style.display=on?'block':'none'; }
}
function startLocalTimer(prefix){
  stopLocalTimer();
  window.aiSec=0;
  aiStatus(prefix+'... 0 сек');
  window.aiT=setInterval(function(){
    window.aiSec+=1;
    aiStatus(prefix+'... '+window.aiSec+' сек');
  },1000);
}
function stopLocalTimer(){
  if(window.aiT){ clearInterval(window.aiT); window.aiT=null; }
}
function reloadSoon(sec){
  stopLocalTimer();
  prog(true);
  aiStatus('Сервер перезапускается... авто-перезагрузка через '+sec+' сек');
  var t=setInterval(function(){
    sec-=1;
    if(sec<=0){ clearInterval(t); location.reload(); }
    else { aiStatus('Сервер перезапускается... авто-перезагрузка через '+sec+' сек'); }
  },1000);
}
function setResult(t){
  document.getElementById('patchResult').textContent=t;
}
function aiCodeFrom(t){
  t=t||'';
  if(t.indexOf('===PATCH===')>=0){
    return t.split('===PATCH===')[1].split('===END===')[0];
  }
  if(t.indexOf('```python')>=0){
    return t.split('```python')[1].split('```')[0];
  }
  return '';
}
function aiCode(){ return aiCodeFrom(window.lastAi); }
function stopPolling(){ if(jobTimer){ clearInterval(jobTimer); jobTimer=null; } }
function pollJob(){
  fetch('/api/admin/job?pin='+encodeURIComponent(getPin()))
  .then(function(r){ return r.json(); })
  .then(function(j){
    renderLog(j.lines||[]);
    if(j.state==='running'){
      prog(true);
      var last=(j.lines||[]).slice(-1)[0]||'';
      aiStatus('Процесс идёт ('+j.sec+' сек): '+last);
    } else {
      prog(false);
      stopPolling();
      if(j.state==='done'||j.state==='error'){
        var res=j.result||{};
        var NL=String.fromCharCode(10);
        var head='Задача "'+j.kind+'" завершена: '+j.state+NL;
        setResult(head+NL+(res.out||'')+NL+NL+'Ответ нейронки:'+NL+(res.ai||''));
        if(res.ai){ window.lastAi=res.ai; }
        var b=document.getElementById('applyAiBtn');
        if(b){ b.style.display=aiCode()?'inline-block':'none'; }
        if(res.rc===0 && (j.kind==='gh'||j.kind==='selfheal')){
          reloadSoon(7);
        } else {
          aiStatus('Готово.');
        }
      }
    }
  })
  .catch(function(){});
}
function startPolling(){
  stopPolling();
  jobTimer=setInterval(pollJob,2000);
  pollJob();
}
function startJob(kind,payload,confirmText){
  if(confirmText && !confirm(confirmText)) return;
  logLine('> запускаю задачу: '+kind);
  payload=payload||{};
  payload.pin=getPin();
  payload.kind=kind;
  fetch('/api/admin/job',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(payload)})
  .then(function(r){
    logLine('> ответ HTTP '+r.status);
    return r.json();
  })
  .then(function(res){
    if(res.busy){ alert('Уже идёт задача - смотрите живой лог'); startPolling(); return; }
    startPolling();
  })
  .catch(function(e){ logLine('> ОШИБКА запуска: '+e.message); alert('Ошибка запуска: '+e.message); });
}
function selfHeal(){
  startJob('selfheal',{},'Запустить самопочинку Qwen? Создам бэкап.');
}
function ghUpdate(){
  var u=document.getElementById('ghUrl').value;
  if(!u){ alert('Впишите GitHub raw-URL один раз - дальше запомнится'); return; }
  var tok=(document.getElementById('ghToken')||{}).value||'';
  startJob('gh',{url:u,token:tok});
}
function askAi(withDiag){
  var p=document.getElementById('aiPrompt').value||'Что чинить в этом коде?';
  startJob('ai',{prompt:p,with_diag:withDiag});
}
function applyAiPatch(){
  var code=aiCode();
  if(!code){ alert('В ответе нейронки не найден код'); return; }
  if(!confirm('Применить патч нейронки и перезапустить?')) return;
  logLine('> применяю патч нейронки');
  prog(true);
  startLocalTimer('Применяю патч нейронки');
  fetch('/api/admin/apply',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({pin:getPin(),code:code,restart:true})})
  .then(function(r){ logLine('> ответ HTTP '+r.status); return r.json(); })
  .then(function(res){
    stopLocalTimer();
    var NL=String.fromCharCode(10);
    setResult('rc='+res.rc+NL+(res.out||''));
    if(res.rc===0){ reloadSoon(8); } else { prog(false); aiStatus('Готово.'); }
  })
  .catch(function(e){ stopLocalTimer(); prog(false); alert('Ошибка: '+e.message); });
}
function applyPatch(restart){
  logLine('> применить патч (restart='+restart+')');
  var code=document.getElementById('patchArea').value;
  if(!code.trim()){ alert('Вставьте код патча'); return; }
  prog(true);
  startLocalTimer('Применяю патч');
  fetch('/api/admin/apply',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({pin:getPin(),code:code,restart:restart})})
  .then(function(r){ logLine('> ответ HTTP '+r.status); return r.json(); })
  .then(function(res){
    stopLocalTimer();
    var NL=String.fromCharCode(10);
    setResult('Код возврата: '+res.rc+NL+NL+(res.out||''));
    logLine('> готово, rc='+res.rc);
    if(restart && res.rc===0){ reloadSoon(8); }
    else { prog(false); aiStatus('Готово.'); }
  })
  .catch(function(e){ stopLocalTimer(); prog(false); logLine('> ОШИБКА: '+e.message); alert('Ошибка: '+e.message); });
}
function showDiag(){
  logLine('> диагностика');
  prog(true);
  startLocalTimer('Собираю диагностику');
  fetch('/api/admin/diag?pin='+encodeURIComponent(getPin()))
  .then(function(r){ logLine('> ответ HTTP '+r.status); return r.json(); })
  .then(function(res){
    stopLocalTimer();
    prog(false);
    var NL=String.fromCharCode(10);
    var L=[];
    L.push('Синтаксис: '+res.syntax);
    L.push('Маршруты:');
    Object.keys(res.markers||{}).forEach(function(k){
      L.push((res.markers[k]?'  OK  ':'  BAD ')+k);
    });
    L.push('Эндпоинты:');
    Object.keys(res.endpoints||{}).forEach(function(k){
      L.push((res.endpoints[k]===200?'  OK  ':'  BAD ')+k+' -> '+res.endpoints[k]);
    });
    L.push('Таблицы: '+(res.tables||[]).join(', '));
    L.push('ollama: '+JSON.stringify(res.ollama_models||''));
    L.push('Лог:');
    L.push(res.log_tail||'');
    setResult(L.join(NL));
    aiStatus('Готово.');
  })
  .catch(function(e){ stopLocalTimer(); prog(false); logLine('> ОШИБКА: '+e.message); alert('Ошибка: '+e.message); });
}
function showUpdates(){
  fetch('/api/admin/updates?pin='+encodeURIComponent(getPin()))
  .then(function(r){ return r.json(); })
  .then(function(rows){
    var h='';
    rows.forEach(function(x){
      h+='<div style="background:#fff;padding:.5rem;margin:.3rem 0;border-radius:6px;">'+x.ts+' | '+x.source+' | rc='+x.rc+'<br><small>'+(x.out||'').slice(0,300)+'</small></div>';
    });
    document.getElementById('histBox').innerHTML=h||'<p>Пусто</p>';
  });
}
function showBackups(){
  fetch('/api/admin/backups?pin='+encodeURIComponent(getPin()))
  .then(function(r){ return r.json(); })
  .then(function(res){
    var h='';
    (res.backups||[]).forEach(function(f){
      h+='<div style="background:#fff;padding:.5rem;margin:.3rem 0;border-radius:6px;">'+f+' <button class="btn btn-danger" style="padding:2px 8px;" data-name="'+f+'" onclick="rb(this.dataset.name)">Откатить</button></div>';
    });
    document.getElementById('histBox').innerHTML=h||'<p>Пусто</p>';
  });
}
function rb(name){
  if(!confirm('Откат до '+name+'?')) return;
  fetch('/api/admin/rollback',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({pin:getPin(),name:name})})
  .then(function(r){ return r.json(); })
  .then(function(res){ setResult(res.out||''); reloadSoon(7); });
}
window.onload=function(){
  var b=document.getElementById('jsBadge');
  if(b){ b.textContent='JS жив ✅'; b.style.color='#27ae60'; }
  var p=localStorage.getItem('swhpin');
  if(p){ document.getElementById('adminPin').value=p; }
  fetch('/api/notes/github_raw_url').then(function(r){ return r.json(); }).then(function(res){
    var el=document.getElementById('ghUrl');
    if(el && res.content && res.content.indexOf('http')===0){ el.value=res.content; }
  }).catch(function(){});
  logLine('Страница загружена, JS жив.');
  fetch('/api/admin/job?pin='+encodeURIComponent(getPin()))
  .then(function(r){ return r.json(); })
  .then(function(j){ if(j.state==='running'){ startPolling(); } })
  .catch(function(){});
};
'''
os.makedirs('static', exist_ok=True)
open('static/admin.js', 'w').write(js)
print('ok: admin.js v7 (авто-перезагрузка, таймеры, подробности)')
print('v7 готов')