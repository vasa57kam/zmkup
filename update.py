import os
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
    import ast as _ast
    import shutil
    base = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(base, 'patch_tmp.py')
    open(fn, 'w').write(code)
    backup_path = make_backup()
    p = subprocess.run(['python3', fn], cwd=base, capture_output=True, text=True, timeout=300)
    out = (p.stdout or '') + (p.stderr or '')
    rc = p.returncode
    if rc == 0:
        try:
            _ast.parse(open(os.path.join(base, 'swh.py')).read())
        except Exception as e:
            shutil.copy(backup_path, os.path.join(base, 'swh.py'))
            out += ' || ПАТЧ СЛОМАЛ swh.py - АВТООТКАТ из бэкапа: ' + str(e)[:200]
            rc = -6
    log_update(source, rc, out, code)
    return rc, out

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
              'ВАЖНО: никогда не используй экранированные кавычки вида backslash-апостроф. '
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
    print('ok: job-инфраструктура + автооткат битых патчей')
else:
    print('job уже на месте')

import ast
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис чистый')