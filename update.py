import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Скрипт полного удаления + эндпоинт
if 'UNINSTALL_SH' not in src:
    UN = '''UNINSTALL_SH = """#!/bin/bash
DIR="${1:-$(cd "$(dirname "$0")" && pwd)}"
echo "=== Полное удаление панели в $DIR ==="
pkill -f "python3 $DIR/swh.py" 2>/dev/null
pkill -f "python3 swh.py" 2>/dev/null
sleep 2
( crontab -l 2>/dev/null | grep -v 'swh.py' ) | crontab - 2>/dev/null
if [ "$FULL" == "1" ]; then
  echo '=== Сносим поставленные пакеты ==='
  apt-get remove -y snmp sshpass traceroute 2>/dev/null
  pip3 uninstall -y flask flask-cors 2>/dev/null
fi
cd /tmp
rm -rf "$DIR"
rm -f /tmp/swh_uninstall.sh
echo '=== Панель удалена полностью. Сервер как до установки. ==='
"""

@app.route('/api/admin/uninstall', methods=['POST'])
def admin_uninstall():
    import subprocess
    import threading
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN or d.get('confirm') != 'УДАЛИТЬ':
        return jsonify({'error': 'нужен PIN и слово подтверждения УДАЛИТЬ'}), 403
    base = os.path.dirname(os.path.abspath(__file__))
    sh = '/tmp/swh_uninstall.sh'
    open(sh, 'w').write(UNINSTALL_SH)
    os.chmod(sh, 0o755)
    env = dict(os.environ)
    env['FULL'] = '1' if d.get('full') else '0'
    subprocess.Popen(['bash', sh, base], env=env, start_new_session=True)
    threading.Timer(3.0, lambda: os._exit(0)).start()
    return jsonify({'ok': True, 'out': 'Удаление запущено: процесс остановлен, cron снят, файлы стираются.'})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + UN + src[idx:]
    print('ok: uninstall.sh + эндпоинт')

# 2) uninstall.sh внутрь миграционного архива
rep("""        t.add(dep, arcname='swh_migrate/deploy.sh')
    os.remove(dep)""",
"""        t.add(dep, arcname='swh_migrate/deploy.sh')
        dep2 = os.path.join(base, 'uninstall_tmp.sh')
        open(dep2, 'w').write(UNINSTALL_SH)
        t.add(dep2, arcname='swh_migrate/uninstall.sh')
        os.remove(dep2)
    os.remove(dep)""", 'uninstall.sh в архиве')

# 3) Кнопка в админке
rep('<button class="btn btn-primary" onclick="migrate()">🚚 Миграция: собрать архив</button>',
    '<button class="btn btn-primary" onclick="migrate()">🚚 Миграция: собрать архив</button>\n<button class="btn" style="background:#c0392b;" onclick="uninstallPanel()">☠️ Полное удаление</button>',
    'кнопка полного удаления')

# 4) JS кнопки
import os
ajs_path = os.path.join('static', 'admin.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'function uninstallPanel()' not in ajs:
    ajs += '''
function uninstallPanel(){
  if(!confirm('ПОЛНОЕ удаление панели с ЭТОГО сервера? Наряды, фото, база, бэкапы будут СТЁРТЫ!')) return;
  var w=prompt('Введите слово УДАЛИТЬ для подтверждения:');
  if(w!=='УДАЛИТЬ'){ alert('Отменено'); return; }
  fetch('/api/admin/uninstall',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({pin:getPin(), confirm:'УДАЛИТЬ', full:false})})
  .then(function(){ alert('Удаление запущено. Сервер скоро перестанет отвечать — это нормально.'); })
  .catch(function(){ alert('Сервер уже гаснет — удаление идёт.'); });
}
'''
    open(ajs_path, 'w').write(ajs)
    print('ok: admin.js uninstallPanel')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')