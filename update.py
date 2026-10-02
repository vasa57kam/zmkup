import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Эндпоинты автозапуска (cron keepalive + @reboot)
if "'/api/admin/autostart'" not in src:
    ep = '''
@app.route('/api/admin/autostart', methods=['GET', 'POST'])
def admin_autostart():
    import subprocess
    base = os.path.dirname(os.path.abspath(__file__))
    if request.method == 'GET':
        if request.args.get('pin') != ADMIN_PIN:
            return jsonify({'error': 'pin'}), 403
        cur = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        return jsonify({'enabled': 'swh.py' in (cur.stdout or '')})
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    enable = bool(d.get('enable'))
    cur = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    lines = [l for l in (cur.stdout or '').splitlines() if l.strip() and 'swh.py' not in l]
    if enable:
        lines.append('* * * * * cd ' + base + ' && (curl -s -o /dev/null --max-time 3 http://localhost:9500/ || nohup python3 swh.py >> swh.log 2>&1 &)')
        lines.append('@reboot sleep 5 && cd ' + base + ' && nohup python3 swh.py >> swh.log 2>&1 &')
    p = subprocess.run(['crontab', '-'], input='\\n'.join(lines) + '\\n', capture_output=True, text=True)
    if p.returncode != 0:
        return jsonify({'error': 'crontab: ' + (p.stderr or '')[:200]}), 500
    return jsonify({'ok': True, 'enabled': enable})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    print('ok: /api/admin/autostart')

# 2) README.txt в миграционный архив
if 'readme_tmp.txt' not in src:
    rep("        t.add(dep, arcname='swh_migrate/deploy.sh')",
"""        rd = os.path.join(base, 'readme_tmp.txt')
        open(rd, 'w').write(README_TXT)
        t.add(rd, arcname='swh_migrate/README.txt')
        os.remove(rd)
        t.add(dep, arcname='swh_migrate/deploy.sh')""", 'README в архиве')

if 'README_TXT = ' not in src:
    RT = '''README_TXT = """УСТАНОВКА И УДАЛЕНИЕ ПАНЕЛИ ЗАМЕНЫ КОММУТАТОРОВ
================================================
1) Распаковать архив:  tar xzf swh_migrate_*.tar.gz
2) Перейти в папку:   cd swh_migrate
3) Установить и запустить:  bash deploy.sh
   (поставит flask/snmp/sshpass/traceroute, поднимет панель на порту 9500,
    пропишет автозапуск после перезагрузки и сторожа каждую минуту)
4) Автозапуск вкл/выкл: админка -> блок «🔄 Автозапуск» (кнопки Включить/Выключить).
5) Полное удаление со всеми следами:  bash uninstall.sh
   вместе с системными пакетами:      FULL=1 bash uninstall.sh
6) Все данные лежат в этой папке: база нарядов/камер/VLAN, фото (uploads),
   бэкапы (backups). Архив храните как точку отката.
7) Ollama-модели на новый сервер ставятся отдельно (без них панель работает,
   кнопки ИИ скажут «ollama недоступна»).
"""

'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + RT + src[idx:]
    print('ok: README_TXT')

# 3) Блок автозапуска в админке
if 'id="asStatus"' not in src:
    rep('<button class="btn" style="background:#c0392b;" onclick="uninstallPanel()">☠️ Полное удаление</button>',
"""<button class="btn" style="background:#c0392b;" onclick="uninstallPanel()">☠️ Полное удаление</button>
<div style="background:#fff;padding:1rem;border-radius:8px;margin:1rem 0;">
<h3>🔄 Автозапуск после ребута и обновлений</h3>
<p id="asStatus" style="color:#7f8c8d;">Статус: проверяю…</p>
<button class="btn btn-success" onclick="autostartSet(true)">✅ Включить автозапуск</button>
<button class="btn btn-secondary" onclick="autostartSet(false)">⛔ Выключить автозапуск</button>
<small style="display:block;margin-top:.5rem;color:#7f8c8d;">Когда включено: cron поднимает панель сам после перезагрузки сервера и после любого обновления с перезапуском (проверка каждую минуту). Выключили — панель живёт только до ребута.</small>
</div>""", 'блок автозапуска в админке')

# 4) JS админки
import os
ajs_path = os.path.join('static', 'admin.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'function loadAutostart()' not in ajs:
    ajs += '''
function loadAutostart(){
  var el=document.getElementById('asStatus');
  if(!el) return;
  fetch('/api/admin/autostart?pin='+encodeURIComponent(getPin())).then(function(r){return r.json();}).then(function(res){
    el.textContent='Статус: '+(res.enabled? 'ВКЛЮЧЕН (cron-сторож каждую минуту + автозапуск после ребута)' : 'ВЫКЛЮЧЕН (панель не поднимется сама после ребута)');
  }).catch(function(){ el.textContent='Статус: неизвестен'; });
}
function autostartSet(on){
  fetch('/api/admin/autostart',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:getPin(), enable:on})})
  .then(function(r){return r.json();}).then(function(res){
    alert(res.ok? (on? 'Автозапуск ВКЛЮЧЁН' : 'Автозапуск ВЫКЛЮЧЕН') : 'Ошибка: '+(res.error||''));
    loadAutostart();
  });
}
'''
    ajs = ajs.replace("  if(document.getElementById('clList')){ loadCL(); }",
"""  if(document.getElementById('clList')){ loadCL(); }
  loadAutostart();""", 1)
    open(ajs_path, 'w').write(ajs)
    print('ok: admin.js автозапуск')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')