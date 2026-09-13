import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Кнопка миграции + эндпоинты архива
if "'/api/admin/migrate'" not in src:
    ep = '''
DEPLOY_SH = """#!/bin/bash
set -e
cd "$(dirname "$0")"
echo '=== Развёртывание панели замены коммутаторов ==='
apt-get update && apt-get install -y python3-pip snmp sshpass traceroute || true
pip3 install flask flask-cors || apt-get install -y python3-flask python3-flask-cors || true
( crontab -l 2>/dev/null | grep -v 'swh.py' ; echo "* * * * * cd $PWD && (curl -s -o /dev/null --max-time 3 http://localhost:9500/ || nohup python3 swh.py >> swh.log 2>&1 &)" ; echo "@reboot sleep 5 && cd $PWD && nohup python3 swh.py >> swh.log 2>&1 &" ) | crontab -
nohup python3 swh.py > swh.log 2>&1 &
sleep 3
echo '=== Готово: http://<IP_ЭТОГО_СЕРВЕРА>:9500/ ==='
echo 'PIN прежний. Ollama-модели при необходимости поставьте отдельно на новом сервере.'
"""

@app.route('/api/admin/migrate', methods=['POST'])
def migrate_create():
    import tarfile
    from datetime import datetime
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    base = os.path.dirname(os.path.abspath(__file__))
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    name = 'swh_migrate_' + ts + '.tar.gz'
    path = os.path.join(base, name)
    dep = os.path.join(base, 'deploy_tmp.sh')
    open(dep, 'w').write(DEPLOY_SH)
    with tarfile.open(path, 'w:gz') as t:
        for item in ('swh.py', 'passport_mod.py', 'switch_replacements.db', 'static', 'uploads', 'backups'):
            p = os.path.join(base, item)
            if os.path.exists(p):
                t.add(p, arcname='swh_migrate/' + item)
        t.add(dep, arcname='swh_migrate/deploy.sh')
    os.remove(dep)
    return jsonify({'file': name,
                    'size_mb': round(os.path.getsize(path) / 1048576.0, 1),
                    'url': '/api/admin/migrate_get?f=' + name + '&pin=' + ADMIN_PIN})

@app.route('/api/admin/migrate_get')
def migrate_get():
    f = os.path.basename(request.args.get('f', ''))
    if not (f.startswith('swh_migrate_') and f.endswith('.tar.gz')):
        return jsonify({'error': 'плохое имя'}), 400
    if request.args.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), f, as_attachment=True)


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    print('ok: эндпоинты миграции')

rep('<button class="btn btn-success" onclick="autoWish()">🤖 Автономка: воплотить желание</button>',
    '<button class="btn btn-success" onclick="autoWish()">🤖 Автономка: воплотить желание</button>\n<button class="btn btn-primary" onclick="migrate()">🚚 Миграция: собрать архив</button>',
    'кнопка миграции')

# 2) admin.js: функция migrate()
import os
ajs_path = os.path.join('static', 'admin.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'function migrate()' not in ajs:
    ajs += '''
function migrate(){
  if(!confirm('Собрать архив миграции (всё: код, база, фото, бэкапы)?')) return;
  fetch('/api/admin/migrate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:getPin()})})
  .then(function(r){return r.json();}).then(function(res){
    if(res.url){
      alert('Архив готов: '+res.file+' ('+res.size_mb+' MB). Скачивание началось.');
      location.href=res.url;
    } else {
      alert('Ошибка: '+(res.error||'неизвестно'));
    }
  }).catch(function(e){ alert('Ошибка: '+e.message); });
}
'''
    open(ajs_path, 'w').write(ajs)
    print('ok: admin.js migrate()')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')