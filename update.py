import ast, json, os, re, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v17_' + TS + '.py')
src = open('swh.py', encoding='utf-8').read()
FIXES = []
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); FIXES.append(label); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) КРИТИЧНО: убрать debug-консоль наружу + многопоточность
rep("app.run(host='0.0.0.0', port=9500, debug=True, use_reloader=False)",
    "app.run(host='0.0.0.0', port=9500, debug=False, use_reloader=False, threaded=True)",
    'debug=False + threaded=True')

# 2) init_db: создание недостающих таблиц и колонок (чистая установка не упадёт)
if 'CREATE TABLE IF NOT EXISTS region_vlans' not in src:
    rep("    conn.commit()\n    cursor = conn.cursor()",
"""    for _stmt in (
        "CREATE TABLE IF NOT EXISTS commands_dict (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, body TEXT, notes TEXT)",
        "CREATE TABLE IF NOT EXISTS change_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, source TEXT, message TEXT)",
        "CREATE TABLE IF NOT EXISTS cameras (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, side TEXT, model TEXT, serial TEXT, ip TEXT, mac TEXT, zone TEXT, notes TEXT, config_text TEXT)",
        "CREATE TABLE IF NOT EXISTS region_vlans (id INTEGER PRIMARY KEY AUTOINCREMENT, region TEXT, switch_ip TEXT, segment TEXT, vlan INTEGER, UNIQUE(region, vlan))",
        "CREATE TABLE IF NOT EXISTS kb_articles (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, tags TEXT, body TEXT, schema TEXT, created_at TEXT)",
    ):
        try:
            conn.execute(_stmt)
        except Exception:
            pass
    for _tbl, _cols in (('work_orders', ('order_type TEXT', 'old_podyezd TEXT', 'new_podyezd TEXT', 'new_switch_location TEXT')),
                        ('cameras', ('login TEXT', 'password TEXT', 'rtsp TEXT', 'vlan TEXT', 'port TEXT', 'switch_name TEXT', 'switch_port TEXT'))):
        for _c in _cols:
            try:
                conn.execute('ALTER TABLE ' + _tbl + ' ADD COLUMN ' + _c)
            except Exception:
                pass
    conn.commit()
    cursor = conn.cursor()""", 'init_db: недостающие таблицы/колонки')

# 3) CSS: селекты не рвут модалки и страницы
if 'def inject_select_fix' not in src:
    ep = '''
@app.after_request
def inject_select_fix(resp):
    try:
        if 'text/html' in (resp.content_type or ''):
            t = resp.get_data(as_text=True)
            if '</head>' in t and 'select{max-width:100%}' not in t:
                t = t.replace('</head>', '<style>select{max-width:100%;}</style></head>', 1)
                resp.set_data(t)
    except Exception:
        pass
    return resp


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    FIXES.append('CSS select max-width'); print('  ok: CSS select max-width')

# 4) Сброс кэша common.js
rep('<script src="/static/common.js?v=2"></script>', '<script src="/static/common.js?v=4"></script>', 'common.js v4 (base)')
rep('<script src="/static/common.js?v=3"></script>', '<script src="/static/common.js?v=4"></script>', 'common.js v4 (kb)')

# 5) Полный чек-ап
if "'/api/admin/health'" not in src:
    ep = '''
@app.route('/api/admin/health')
def admin_health():
    import urllib.request
    import subprocess
    if request.args.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    want = ['/', '/map', '/commands', '/admin', '/stock', '/field', '/tools', '/gen', '/vlans', '/kb',
            '/order/<int:order_id>', '/planner/<int:order_id>', '/fdb/<int:order_id>', '/passport/<int:order_id>',
            '/api/admin/job', '/api/admin/apply', '/api/admin/ghupdate', '/api/admin/selfheal',
            '/api/cameras', '/api/changelog', '/api/vlans', '/api/kb']
    have = set(str(r) for r in app.url_map.iter_rules())
    ui = {}
    for u, m in (('/gen', 'gen.js'), ('/vlans', 'vlanspage.js'), ('/kb', 'kb.js'), ('/', 'orderSearch'), ('/admin', 'admin.js')):
        try:
            t = urllib.request.urlopen('http://localhost:9500' + u, timeout=5).read().decode()
            ui[u] = 'ok' if m in t else 'BAD:' + m
        except Exception as e:
            ui[u] = 'ERR'
    gj = {}
    try:
        g = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'gen.js'), encoding='utf-8').read()
        gj = {'alias_dlink': 'TPL.dlink=TPL.des' in g, 'ism_swap': 'ism_swap' in g, 'show_log': 'show_log' in g, 'size': len(g)}
    except Exception:
        gj = {'error': 'gen.js не читается'}
    try:
        cr = subprocess.run(['crontab', '-l'], capture_output=True, text=True).stdout or ''
        autostart = 'swh.py' in cr
    except Exception:
        autostart = None
    stamp = {}
    try:
        stamp = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update_stamp.json'), encoding='utf-8'))
    except Exception:
        pass
    return jsonify({'routes_missing': [w for w in want if w not in have], 'ui': ui,
                    'vlans_count': _vlans_count(), 'files_missing': _missing_files(),
                    'genjs': gj, 'autostart': autostart, 'debug': app.debug, 'stamp': stamp})


@app.route('/api/vlans/export')
def vlans_export():
    conn = get_db()
    ensure_vlans(conn)
    rows = conn.execute('SELECT region, switch_ip, segment, vlan FROM region_vlans ORDER BY region, vlan').fetchall()
    conn.close()
    out = io.StringIO()
    w = csv.writer(out, delimiter=';')
    w.writerow(['Район', 'IP-адрес свитча', 'Сегмент (VLAN)', 'Номер VLAN'])
    for r in rows:
        w.writerow([r['region'], r['switch_ip'], r['segment'], r['vlan']])
    return Response(out.getvalue().encode('utf-8-sig'), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=vlans_backup.csv'})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    FIXES.append('health + csv export'); print('  ok: /api/admin/health + /api/vlans/export')

rep('<button class="btn btn-primary" onclick="migrate()">🚚 Миграция: собрать архив</button>',
    '<button class="btn btn-primary" onclick="migrate()">🚚 Миграция: собрать архив</button>\n<button id="healthBtn" class="btn btn-success" onclick="healthCheck()">🩺 Полный чек-ап</button>',
    'кнопка чек-апа')
rep('<div class="card"><b>➕ Добавить строку</b>',
    '<div class="card"><a class="btn" style="background:#3498db;" href="/api/vlans/export">📤 Скачать CSV (бэкап справочника)</a></div>\n<div class="card"><b>➕ Добавить строку</b>',
    'кнопка CSV на /vlans')

ajs = open('static/admin.js', encoding='utf-8').read() if os.path.exists('static/admin.js') else ''
if 'function healthCheck()' not in ajs:
    ajs += '''
function healthCheck(){
  fetch('/api/admin/health?pin='+encodeURIComponent(getPin())).then(function(r){return r.json();}).then(function(h){
    var L=[];
    L.push('Версия: '+((h.stamp||{}).version||'нет штампа')+' от '+((h.stamp||{}).ts||'?'));
    L.push('debug: '+h.debug+' (должен быть false)');
    L.push('Маршруты отсутствуют: '+((h.routes_missing||[]).join(', ')||'нет'));
    Object.keys(h.ui||{}).forEach(function(k){ L.push('UI '+k+': '+h.ui[k]); });
    L.push('VLANов в БД: '+h.vlans_count);
    L.push('Файлов-призраков: '+((h.files_missing||[]).join(', ')||'0'));
    L.push('gen.js: '+JSON.stringify(h.genjs));
    L.push('Автозапуск: '+h.autostart);
    alert(L.join('\\n'));
  }).catch(function(e){ alert('Ошибка: '+e.message); });
}
'''
    open('static/admin.js', 'w', encoding='utf-8').write(ajs)
    FIXES.append('admin.js healthCheck'); print('  ok: admin.js healthCheck')

# 6) gen.js: show log + ism_group, версия v17
gp = 'static/gen.js'
if os.path.exists(gp):
    shutil.copyfile(gp, gp + '.bak17')
    g = open(gp, encoding='utf-8').read()
    if 'show_log' not in g:
        g2 = re.sub(r"(['\"])ddm_all\1(\s*:\s*)(['\"])show ddm\3",
                    lambda m: m.group(0) + ",\n  'show_log': 'show log',\n  'ism_group': 'show igmp_snooping group vlan vlan{vlan}'",
                    g, count=2)
        g2 = re.sub(r"(['\"])t2a\1(\s*:\s*)(['\"])[^'\"]*\3(\s*})",
                    lambda m: m.group(0)[:-len(m.group(4))] + ", 'show_log': 'Показать лог свитча (show log)', 'ism_group': 'ISM: multicast-группы по VLAN'" + m.group(4),
                    g2, count=1)
        if 'show_log' in g2:
            g = g2
            open(gp, 'w', encoding='utf-8').write(g)
            FIXES.append('gen.js show_log/ism_group'); print('  ok: gen.js + show_log/ism_group')
        else:
            print('  ПРОПУСК: gen.js якоря не найдены (файл не тронут)')
    else:
        print('  gen.js: show_log уже есть')
new_src, n = re.subn(r'/static/gen\.js\?v=\d+', '/static/gen.js?v=17', src)
if n:
    src = new_src; FIXES.append('gen.js v17'); print('  ok: gen.js -> v17')

# 7) Штамп + проверка + запись
try:
    ast.parse(src)
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v17_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откатил swh.py: ' + str(e))
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v17', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v17. Применено:', len(FIXES), 'правок. Бэкап: backups/swh_pre_v17_' + TS + '.py')
