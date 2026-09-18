import os, json, shutil, subprocess, time, sys
D = "/opt/agent-panel"
rep = []
mp = os.path.join(D, "main.py"); pp = os.path.join(D, "page.html"); bp = os.path.join(D, "builder.py")
shutil.copy2(mp, "/tmp/main.py.preupd")
s = open(mp, errors="ignore").read(); orig = s

# 1) импорт StreamingResponse (без якорей-замен)
if 'StreamingResponse' not in s:
    if 'from fastapi import FastAPI, Request' in s:
        s = s.replace('from fastapi import FastAPI, Request', 'from fastapi import FastAPI, Request\nfrom fastapi.responses import StreamingResponse', 1)
    else:
        s = 'from fastapi.responses import StreamingResponse\n' + s
    rep.append("main: импорт StreamingResponse")

# 2) /api/ask: ВЫРЕЗАТЬ старый блок по границам и вставить стриминг
i = s.find('@app.post("/api/ask")')
if i != -1:
    j = len(s)
    for em in ('\n@app.', '\ndef ollama_gen'):
        k = s.find(em, i + 10)
        if k != -1: j = min(j, k)
    newask = '''@app.post("/api/ask")
def api_ask(d: AskModel):
    q = (d.text or "").strip()
    if not q:
        return JSONResponse({"error": "пустой вопрос"}, 400)
    model = d.model or ACTIVE_MODEL
    import queue, threading
    Q = queue.Queue()
    def producer():
        try:
            ollama_gen(model, q, timeout=1800, on_chunk=lambda pc: Q.put(pc))
            Q.put("__DONE__")
        except Exception as e:
            Q.put("__ERR__:" + str(e)[:200])
    threading.Thread(target=producer, daemon=True).start()
    def stream():
        while True:
            try:
                piece = Q.get(timeout=30)
            except Exception:
                yield 'data: __TO__\\n\\n'; return
            if piece == "__DONE__":
                yield 'data: [DONE]\\n\\n'; return
            if isinstance(piece, str) and piece.startswith("__ERR__:"):
                yield 'data: ' + json.dumps({"err": piece[6:]}) + '\\n\\n'; return
            yield 'data: ' + json.dumps({"c": piece}) + '\\n\\n'
    return StreamingResponse(stream(), media_type="text/event-stream")

'''
    s = s[:i] + newask + s[j:]
    rep.append("main: /api/ask → стриминг (вырезано по границам)")
if 'class AskModel' not in s:
    s = s.replace('@app.post("/api/ask")', 'class AskModel(BaseModel):\n    text: str = ""\n    model: str = ""\n\n@app.post("/api/ask")', 1)
    if 'from pydantic import BaseModel' not in s:
        s = s.replace('from fastapi import FastAPI, Request', 'from fastapi import FastAPI, Request\nfrom pydantic import BaseModel', 1)
    rep.append("main: AskModel")

# 3) настройки генерации: эндпоинты + использование в ollama_gen
if '@app.get("/api/gen")' not in s and '@app.get("/api/tasks")' in s:
    s = s.replace('@app.get("/api/tasks")', '@app.get("/api/gen")\ndef api_gen_get():\n    return SETTINGS.get("gen", {"temp": 0.2, "num_predict": 6000, "num_ctx": 8192, "top_p": 0.9})\n\n@app.post("/api/gen")\nasync def api_gen_set(req: Request):\n    d = await req.json()\n    g = SETTINGS.get("gen", {})\n    for k in ("temp", "num_predict", "num_ctx", "top_p"):\n        if k in d: g[k] = d[k]\n    SETTINGS["gen"] = g; save_settings()\n    return {"ok": True, "gen": g}\n\n@app.get("/api/tasks")', 1)
    rep.append("main: /api/gen — твои настройки нейросети")
lines = s.split('\n')
for idx, ln in enumerate(lines):
    if ln.startswith('def ollama_gen('):
        lines[idx] = ln.replace('num_predict=16000', 'num_predict=None').replace('temp=0.2', 'temp=None')
        lines.insert(idx + 1, '    _g = SETTINGS.get("gen", {})')
        lines.insert(idx + 2, '    if num_predict is None: num_predict = _g.get("num_predict", 6000)')
        lines.insert(idx + 3, '    if temp is None: temp = _g.get("temp", 0.2)')
        rep.append("main: ollama_gen берёт параметры из настроек")
        break
s = '\n'.join(lines)
lines = s.split('\n')
for idx, ln in enumerate(lines):
    if '"options": {"temperature": temp' in ln:
        ind = ln[:len(ln) - len(ln.lstrip())]
        lines[idx] = ind + '"options": {"temperature": temp, "num_predict": num_predict, "num_ctx": _g.get("num_ctx", 8192), "top_p": _g.get("top_p", 0.9)}}'
        rep.append("main: num_ctx и top_p в options")
        break
s = '\n'.join(lines)

# 4) сборщик EXE: файл + эндпоинт + в список самопатча (нейронка улучшит сама)
open(bp, "w").write('''import os, subprocess, sys, json
def build(project, entry):
    pdir = os.path.expanduser("~/agent-projects/" + project)
    src = os.path.join(pdir, entry)
    if not os.path.exists(src):
        return {"ok": False, "error": "нет файла " + entry + " в " + project}
    out = os.path.join(pdir, "dist"); os.makedirs(out, exist_ok=True)
    log = []
    wine_py = "/opt/wine-python/python.exe"
    if os.path.exists("/usr/bin/wine") and os.path.exists(wine_py):
        r = subprocess.run(["wine", wine_py, "-m", "PyInstaller", "--onefile", "--distpath", out, "--workpath", "/tmp/pyw", "--specpath", "/tmp/pyw", src], capture_output=True, text=True, timeout=3600)
        log.append("wine-pyinstaller: " + (r.stdout + r.stderr)[-400:])
        if r.returncode == 0:
            return {"ok": True, "exe": out + "/" + os.path.splitext(entry)[0] + ".exe", "log": "\\n".join(log)}
    r = subprocess.run([sys.executable, "-m", "PyInstaller", "--onefile", "--distpath", out, "--workpath", "/tmp/pyn", "--specpath", "/tmp/pyn", src], capture_output=True, text=True, timeout=3600)
    log.append("pyinstaller: " + (r.stdout + r.stderr)[-400:])
    if r.returncode == 0:
        return {"ok": True, "exe": out + "/" + os.path.splitext(entry)[0], "log": "\\n".join(log)}
    z = out + "/" + os.path.splitext(entry)[0] + ".pyz"
    r2 = subprocess.run([sys.executable, "-m", "zipapp", src, "-o", z], capture_output=True, text=True)
    log.append("zipapp: " + (r2.stdout + r2.stderr)[-300:])
    return {"ok": r2.returncode == 0, "exe": z if r2.returncode == 0 else None, "log": "\\n".join(log)}
if __name__ == "__main__":
    d = json.load(sys.stdin)
    print(json.dumps(build(d.get("project", ""), d.get("entry", "main.py")), ensure_ascii=False))
''')
rep.append("builder.py создан")
if '@app.post("/api/build")' not in s and '@app.get("/api/tasks")' in s:
    s = s.replace('@app.get("/api/tasks")', '@app.post("/api/build")\ndef api_build(d: dict):\n    r = subprocess.run([sys.executable, os.path.join(DIR, "builder.py")], input=json.dumps(d), capture_output=True, text=True, timeout=3600)\n    try:\n        return json.loads(r.stdout or "{}")\n    except Exception:\n        return {"ok": False, "error": (r.stdout + r.stderr)[-500:]}\n\n@app.get("/api/tasks")', 1)
    rep.append("main: /api/build")
if '"watchdog.sh")' in s and '"builder.py"' not in s:
    s = s.replace('("main.py", "page.html", "watchdog.sh")', '("main.py", "page.html", "watchdog.sh", "builder.py")', 1)
    rep.append("main: builder.py в списке самопатча (нейронка улучшит сама)")

if s != orig:
    open(mp, "w").write(s)

# 5) pyinstaller (тихо, не смертельно при неудаче)
try:
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "pyinstaller"], capture_output=True, timeout=900)
    rep.append("pyinstaller: установлен" if r.returncode == 0 else "pyinstaller: НЕ встал (zipapp-фолбэк останется)")
except Exception:
    rep.append("pyinstaller: пропущен (таймаут)")

# 6) страница: стриминг-askNow (вырезать по границам) + секции настроек и сборщика
pg = open(pp, errors="ignore").read(); o = pg
NEWFN = '''async function askNow(){const q=document.getElementById('askq').value.trim();if(!q)return;
 const st=document.getElementById('askst'), out=document.getElementById('aska');
 st.innerText='⏳ модель думает и печатает…'; out.style.display='block'; out.innerText='';
 try{
  const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:q})});
  const rd=r.body.getReader(); const dec=new TextDecoder(); let buf='';
  while(true){
   const {value,done}=await rd.read(); if(done)break;
   buf+=dec.decode(value,{stream:true});
   const lines=buf.split('\\n'); buf=lines.pop();
   for(const ln of lines){
    if(!ln.startsWith('data: '))continue;
    const p=ln.slice(6);
    if(p==='[DONE]'){st.innerText='✅ готово';return;}
    if(p==='__TO__'){st.innerText='⚠ таймаут';return;}
    try{const jj=JSON.parse(p);
     if(jj.err){st.innerText='⚠ '+jj.err;return;}
     if(jj.c){out.innerText+=jj.c;out.scrollTop=out.scrollHeight;}
    }catch(e){}
   }
  }
 }catch(e){st.innerText='⚠ '+e;}
}'''
i = pg.find('async function askNow')
if i != -1:
    j = pg.find('</script>', i)
    pg = pg[:i] + NEWFN + '\n' + pg[j:]
    rep.append("page: стриминг-вывод ответа")
if 'id="gentemp"' not in pg:
    sec = '''<h2>🎛 Настройки нейросети</h2>
<div class="card">
 темп <input id="gentemp" type="number" step="0.1" min="0" max="2" style="width:80px">
 токенов ответа <input id="genpred" type="number" step="500" min="500" max="16000" style="width:110px">
 контекст <input id="genctx" type="number" step="1024" min="2048" max="32768" style="width:110px">
 top_p <input id="gentopp" type="number" step="0.05" min="0" max="1" style="width:80px">
 <button onclick="saveGen()">💾 Сохранить</button>
</div>
<h2>📦 Сборщик EXE (python → exe)</h2>
<div class="card">
 проект <input id="bproj" placeholder="Inter1" style="width:140px">
 входной файл <input id="bentry" value="main.py" style="width:140px">
 <button onclick="buildExe()">🔨 Собрать EXE</button>
 <span class="hint" id="bst"></span>
 <pre id="blog" style="display:none;max-height:30vh;overflow:auto"></pre>
</div>
'''
    a = pg.find('<h2>💬 Спросить нейронку</h2>')
    if a != -1:
        pg = pg[:a] + sec + pg[a:]
        rep.append("page: секции настроек и сборщика")
if 'function saveGen' not in pg:
    k = pg.rfind('</body>')
    pg = pg[:k] + '''<script>
async function loadGen(){try{const g=await j('/api/gen');$('gentemp').value=g.temp;$('genpred').value=g.num_predict;$('genctx').value=g.num_ctx;$('gentopp').value=g.top_p;}catch(e){}}
async function saveGen(){const r=await j('/api/gen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({temp:+$('gentemp').value,num_predict:+$('genpred').value,num_ctx:+$('genctx').value,top_p:+$('gentopp').value})});alert(r.ok?'параметры сохранены — действуют на все генерации':'ошибка');}
async function buildExe(){$('bst').innerText='🔨 собираю (может занять минуты)…';$('blog').style.display='none';
 const r=await j('/api/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project:$('bproj').value,entry:$('bentry').value})});
 $('bst').innerText=r.ok?('✅ готово: '+r.exe):('❌ '+(r.error||'сборка не удалась'));$('blog').style.display='block';$('blog').innerText=r.log||'';}
loadGen();
</script>
''' + pg[k:]
    rep.append("page: скрипт настроек и сборщика")
if pg != o:
    open(pp, "w").write(pg)

# 7) версия
sp = os.path.join(D, "settings.json")
st = {}
try: st = json.load(open(sp))
except Exception: pass
st["gh_ver"] = "v23"
json.dump(st, open(sp, "w"))
rep.append("settings: gh_ver=v23")

# САМОПРОВЕРКА
r = subprocess.run([sys.executable, "-m", "py_compile", mp], capture_output=True, text=True)
if r.returncode != 0:
    shutil.copy2("/tmp/main.py.preupd", mp)
    print("ЧТО СДЕЛАНО:"); print("\n".join(rep))
    print("UPDATE FAIL: синтаксис бит — main.py восстановлен, панель на старом коде")
    print(r.stderr[-400:])
    raise SystemExit(1)

with open(os.path.join(D, "CHANGELOG.md"), "a") as f:
    f.write("\n### " + time.strftime("%d.%m %H:%M") + " — github-обновление\nv23: " + "; ".join(rep) + "\n")
subprocess.run(["git", "add", "-A"], cwd=D)
subprocess.run(["git", "commit", "-m", "update from github: v23 stream+gen settings+exe builder"], cwd=D)
print("ЧТО СДЕЛАНО:"); print("\n".join(rep))
print("UPDATE OK: v23")