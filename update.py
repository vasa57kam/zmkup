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
        aiStatus('Готово.');
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
  .then(function(r){ return r.json(); })
  .then(function(res){
    if(res.busy){ alert('Уже идёт задача - смотрите живой лог'); startPolling(); return; }
    startPolling();
  })
  .catch(function(e){ alert('Ошибка запуска: '+e.message); });
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
  fetch('/api/admin/apply',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({pin:getPin(),code:code,restart:true})})
  .then(function(r){ return r.json(); })
  .then(function(res){
    prog(false);
    var NL=String.fromCharCode(10);
    setResult('rc='+res.rc+NL+(res.out||''));
  })
  .catch(function(e){ prog(false); alert('Ошибка: '+e.message); });
}
function applyPatch(restart){
  logLine('> применить патч (restart='+restart+')');
  var code=document.getElementById('patchArea').value;
  if(!code.trim()){ alert('Вставьте код патча'); return; }
  prog(true);
  fetch('/api/admin/apply',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({pin:getPin(),code:code,restart:restart})})
  .then(function(r){ return r.json(); })
  .then(function(res){
    prog(false);
    var NL=String.fromCharCode(10);
    setResult('Код возврата: '+res.rc+NL+NL+(res.out||''));
  })
  .catch(function(e){ prog(false); alert('Ошибка: '+e.message); });
}
function showDiag(){
  logLine('> диагностика');
  prog(true);
  fetch('/api/admin/diag?pin='+encodeURIComponent(getPin()))
  .then(function(r){ return r.json(); })
  .then(function(res){
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
  })
  .catch(function(e){ prog(false); alert('Ошибка: '+e.message); });
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
  .then(function(res){ setResult(res.out||''); });
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
print('ok: admin.js v6 (фоновые job)')

src = open('swh.py').read()
if 'def job_log' not in src:
    infra = '''
import threading
import time as _time

JOB = {'state': 'idle', 'lines': [], 'result': None, 'kind': '', 'ts': 0}

def job_log(t):
    JOB['lines'].append(t)
    if len(JOB['lines']) > 300:
        JOB['lines'] = JOB['lines'][-300:]

def _ollama_tags():
    import urllib.request
    import json as _json
    try:
        r = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=10)
        return [m.get('name', '') for m in _json.loads(r.read().decode()).get('models', [])]
    except Exception:
        return []

def _ollama_gen(prompt):
    import urllib.request
    import json as _json
    tags = _ollama_tags()
    if not tags:
        raise RuntimeError('ollama: моделей нет')
    model = 'qwen3-coder:30b'
    if model not in tags:
        model = next((t for t in tags if 'qwen' in t.lower()), tags[0])
    job_log('модель: ' + model)
    body = _json.dumps({'model': model, 'prompt': prompt, 'stream': False}).encode()
    rq = urllib.request.Request('http://localhost:11434/api/generate', data=body, headers={'Content-Type': 'application/json'})
    r = urllib.request.urlopen(rq, timeout=1800)
    return _json.loads(r.read().decode()).get('response', '')

def _diag_text():
    import urllib.request
    import urllib.parse
    u = 'http://localhost:9500/api/admin/diag?pin=' + urllib.parse.quote(ADMIN_PIN)
    return urllib.request.urlopen(u, timeout=30).read().decode()

def _run_patch_code(code, source):
    import subprocess
    base = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(base, 'patch_tmp.py')
    open(fn, 'w').write(code)
    make_backup()
    p = subprocess.run(['python3', fn], cwd=base, capture_output=True, text=True, timeout=300)
    out = (p.stdout or '') + (p.stderr or '')
    log_update(source, p.returncode, out, code)
    return p.returncode, out

def _restart_later():
    import subprocess
    base = os.path.dirname(os.path.abspath(__file__))
    cmd = 'sleep 2; pkill -f swh.py; sleep 1; cd ' + base + ' && nohup python3 swh.py > swh.log 2>&1 &'
    subprocess.Popen(['bash', '-c', cmd], start_new_session=True)

def do_selfheal():
    job_log('самопочинка: читаю диагностику...')
    diag = _diag_text()
    prompt = ('Ты сопровождаешь панель swh.py. Вот диагностика. '
              'Найди ВСЕ неисправности. Дай ОДИН python-патч между ===PATCH=== и ===END===: '
              'читает swh.py, правит через replace с точными якорями, пишет обратно, ast.parse. '
              'Диагностика: ' + diag[:6000])
    job_log('нейронка думает (может занять несколько минут)...')
    text = _ollama_gen(prompt)
    code = ''
    if '===PATCH===' in text:
        code = text.split('===PATCH===')[1].split('===END===')[0]
    elif '```python' in text:
        code = text.split('```python')[1].split('```')[0]
    if not code.strip():
        JOB['result'] = {'ok': False, 'rc': -5, 'out': 'Нейронка не дала код', 'ai': text[:1500]}
        return
    job_log('нейронка дала патч, применяю...')
    rc, out = _run_patch_code(code, 'selfheal')
    JOB['result'] = {'ok': rc == 0, 'rc': rc, 'out': out[-4000:], 'ai': text[:1500]}
    if rc == 0:
        job_log('патч применён, перезапускаю сервер...')
        _restart_later()
    else:
        job_log('патч НЕ применён, rc=' + str(rc))

def do_gh(url, token):
    import urllib.request
    job_log('скачиваю update.py...')
    rq = urllib.request.Request(url)
    if token:
        rq.add_header('Authorization', 'token ' + token)
    code = urllib.request.urlopen(rq, timeout=60).read().decode('utf-8')
    job_log('скачано ' + str(len(code)) + ' байт, применяю...')
    rc, out = _run_patch_code(code, 'github')
    conn = get_db()
    conn.execute("DELETE FROM app_notes WHERE note_key='github_raw_url'")
    conn.execute("INSERT INTO app_notes (note_key, content) VALUES ('github_raw_url', ?)", (url,))
    conn.commit()
    conn.close()
    JOB['result'] = {'ok': rc == 0, 'rc': rc, 'out': out[-4000:]}
    if rc == 0:
        job_log('обновление применено, перезапускаю...')
        _restart_later()

def do_ai(prompt, with_diag):
    if with_diag:
        job_log('собираю диагностику...')
        prompt = prompt + '\\n\\nДиагностика:\\n' + _diag_text()[:6000]
    job_log('нейронка думает...')
    text = _ollama_gen(prompt)
    JOB['result'] = {'ok': True, 'rc': 0, 'out': text[:8000]}
    job_log('ответ готов')

def _job_work(kind, payload):
    try:
        if kind == 'selfheal':
            do_selfheal()
        elif kind == 'gh':
            do_gh(payload.get('url', ''), payload.get('token', ''))
        elif kind == 'ai':
            do_ai(payload.get('prompt', ''), payload.get('with_diag'))
        if JOB['state'] == 'running':
            JOB['state'] = 'done'
    except Exception as e:
        job_log('ошибка: ' + str(e))
        JOB['state'] = 'error'
        JOB['result'] = {'ok': False, 'rc': -9, 'out': str(e)}

@app.route('/api/admin/job', methods=['GET', 'POST'])
def admin_job():
    if request.method == 'GET':
        if request.args.get('pin') != ADMIN_PIN:
            return jsonify({'error': 'pin'}), 403
        sec = int(_time.time() - JOB['ts']) if JOB['ts'] else 0
        return jsonify({'state': JOB['state'], 'lines': JOB['lines'],
                        'sec': sec, 'result': JOB['result'], 'kind': JOB['kind']})
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    if JOB['state'] == 'running':
        return jsonify({'started': False, 'busy': True})
    kind = d.get('kind', '')
    JOB['state'] = 'running'
    JOB['lines'] = []
    JOB['result'] = None
    JOB['kind'] = kind
    JOB['ts'] = _time.time()
    threading.Thread(target=_job_work, args=(kind, d), daemon=True).start()
    return jsonify({'started': True})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + infra + src[idx:]
    open('swh.py', 'w').write(src)
    print('ok: фоновые job на сервере')

import ast
ast.parse(open('swh.py').read())
print('update.py отработал')