import ast, json, os, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v18_' + TS + '.py')
src = open('swh.py', encoding='utf-8').read()
FIXES = []
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); FIXES.append(label); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Недостающий маршрут журнала изменений
if "'/api/changelog'" not in src:
    ep = '''
@app.route('/api/changelog')
def changelog_api():
    conn = get_db()
    try:
        rows = conn.execute('SELECT * FROM change_log ORDER BY id DESC LIMIT 200').fetchall()
    except Exception:
        rows = []
    conn.close()
    return jsonify([dict(r) for r in rows])


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    FIXES.append('/api/changelog'); print('  ok: /api/changelog')

# 2) HTTPS: поиск пары cert/key в папке + эндпоинты настройки
if 'def _detect_certs' not in src:
    ep = '''
def _detect_certs(d):
    import glob
    for c, k in (('fullchain.pem', 'privkey.pem'), ('cert.pem', 'key.pem'), ('fullchain.crt', 'privkey.key')):
        if os.path.isfile(os.path.join(d, c)) and os.path.isfile(os.path.join(d, k)):
            return os.path.join(d, c), os.path.join(d, k)
    crts = [c for c in sorted(glob.glob(os.path.join(d, '*.crt')) + glob.glob(os.path.join(d, '*.pem')))
            if 'key' not in os.path.basename(c).lower()]
    keys = sorted(glob.glob(os.path.join(d, '*.key')))
    if crts and keys:
        return crts[0], keys[0]
    return None, None

def _https_cfg():
    try:
        conn = get_db()
        r = conn.execute("SELECT content FROM app_notes WHERE note_key='https_cfg'").fetchone()
        conn.close()
        return json.loads(r['content']) if r else {}
    except Exception:
        return {}

@app.route('/api/admin/https', methods=['GET', 'POST'])
def admin_https():
    import threading
    if request.method == 'GET':
        if request.args.get('pin') != ADMIN_PIN:
            return jsonify({'error': 'pin'}), 403
        cfg = _https_cfg()
        cert, key = _detect_certs(cfg.get('dir') or '') if cfg.get('dir') else (None, None)
        return jsonify({'cfg': cfg, 'cert': cert, 'key': key})
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    folder = (d.get('dir') or '').strip()
    port = int(d.get('port') or 443)
    enabled = bool(d.get('enabled'))
    cert, key = _detect_certs(folder) if folder else (None, None)
    if enabled and not (cert and key):
        return jsonify({'error': 'в папке не найдена пара cert/key (fullchain.pem+privkey.pem, cert.pem+key.pem или *.crt+*.key)'}), 400
    cfg = {'dir': folder, 'port': port, 'enabled': enabled, 'cert': cert, 'key': key}
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO app_notes (note_key, content) VALUES ('https_cfg', ?)",
                 (json.dumps(cfg, ensure_ascii=False),))
    conn.commit()
    conn.close()
    if d.get('restart'):
        threading.Timer(2.0, lambda: os._exit(0)).start()
    return jsonify({'ok': True, 'cfg': cfg, 'restart': bool(d.get('restart'))})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    FIXES.append('https endpoints'); print('  ok: /api/admin/https + _detect_certs')

# 3) HTTPS-поток при старте (HTTP :9500 остаётся, IP и домен оба работают)
if '_https_serve' not in src:
    rep("    init_db()\n    app.run(host='0.0.0.0', port=9500, debug=False, use_reloader=False, threaded=True)",
"""    init_db()
    _hc = _https_cfg()
    if _hc.get('enabled') and _hc.get('cert') and _hc.get('key'):
        def _https_serve():
            try:
                from werkzeug.serving import run_simple
                run_simple('0.0.0.0', int(_hc.get('port') or 443), app,
                           ssl_context=(_hc['cert'], _hc['key']),
                           use_reloader=False, threaded=True)
            except Exception as e:
                print('HTTPS не поднялся:', e)
        import threading as _th
        _th.Thread(target=_https_serve, daemon=True).start()
        print('🔒 HTTPS поток запущен на порту', _hc.get('port') or 443)
    app.run(host='0.0.0.0', port=9500, debug=False, use_reloader=False, threaded=True)""",
        'HTTPS-поток при старте')

# 4) Блок настройки в админке
if 'id="httpsDir"' not in src:
    rep('<h3>🔄 Автозапуск после ребута и обновлений</h3>',
"""<div style="background:#fff;padding:1rem;border-radius:8px;margin:1rem 0;">
<h3>🔒 HTTPS / сертификаты (IP и домен)</h3>
<p id="httpsStatus" style="color:#7f8c8d;">Статус: проверяю…</p>
Папка с сертификатами: <input id="httpsDir" style="width:340px;" placeholder="/etc/letsencrypt/live/ваш-домен">
Порт: <input id="httpsPort" value="443" style="width:70px;">
<label><input type="checkbox" id="httpsOn"> Включить HTTPS</label><br>
<button class="btn btn-success" onclick="saveHttps(true)">💾 Сохранить и перезапустить</button>
<button class="btn btn-secondary" onclick="saveHttps(false)">💾 Только сохранить</button>
<small style="display:block;margin-top:.5rem;color:#7f8c8d;">HTTP :9500 остаётся (по IP и по домену). HTTPS поднимется на указанном порту после перезапуска. Сертификат должен быть на ваш домен; по IP браузер предупредит о несовпадении имени — это нормально.</small>
</div>
<h3>🔄 Автозапуск после ребута и обновлений</h3>""", 'блок HTTPS в админке')

# 5) admin.js
ajs = open('static/admin.js', encoding='utf-8').read() if os.path.exists('static/admin.js') else ''
if 'function loadHttps()' not in ajs:
    ajs += '''
function loadHttps(){
  var el=document.getElementById('httpsStatus');
  if(!el) return;
  fetch('/api/admin/https?pin='+encodeURIComponent(getPin())).then(function(r){return r.json();}).then(function(h){
    var c=h.cfg||{};
    document.getElementById('httpsDir').value=c.dir||'';
    document.getElementById('httpsPort').value=c.port||443;
    document.getElementById('httpsOn').checked=!!c.enabled;
    el.textContent='Статус: '+(c.enabled? ('включён, порт '+c.port+', cert: '+(h.cert||'НЕ НАЙДЕН')) : 'выключен')+(h.cert? '' : ' (пара cert/key не найдена в папке)');
  }).catch(function(){ el.textContent='Статус: неизвестен'; });
}
function saveHttps(restart){
  var b={pin:getPin(), dir:document.getElementById('httpsDir').value,
         port:parseInt(document.getElementById('httpsPort').value)||443,
         enabled:document.getElementById('httpsOn').checked, restart:restart};
  fetch('/api/admin/https',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)})
  .then(function(r){return r.json();}).then(function(res){
    if(res.ok){ alert(restart? 'Сохранено. Сервер перезапускается — HTTPS поднимется сам (автозапуск включён).' : 'Сохранено. Перезапустите сервер, чтобы применить.'); loadHttps(); }
    else { alert('Ошибка: '+(res.error||'')); }
  }).catch(function(e){ alert('Ошибка: '+e.message); });
}
'''
    ajs = ajs.replace('  loadAutostart();', '  loadAutostart();\n  loadHttps();', 1)
    open('static/admin.js', 'w', encoding='utf-8').write(ajs)
    FIXES.append('admin.js https'); print('  ok: admin.js loadHttps/saveHttps')

# 6) Штамп v18 + проверка + запись
try:
    ast.parse(src)
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v18_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v18', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v18. Правок:', len(FIXES), '| бэкап: backups/swh_pre_v18_' + TS + '.py')
