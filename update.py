import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Новые инструменты в эндпоинте
rep("""        else:
            return jsonify({'error': 'неизвестный инструмент'}), 400""",
"""        elif tool == 'whois':
            if not shutil.which('whois'):
                return jsonify({'error': 'на сервере нет whois: apt-get install -y whois'}), 503
            p = subprocess.run(['whois', tgt], capture_output=True, text=True, timeout=40)
        elif tool == 'myip':
            import urllib.request as _ur
            try:
                ip = _ur.urlopen('https://api.ipify.org?format=text', timeout=10).read().decode().strip()
            except Exception:
                ip = _ur.urlopen('https://ifconfig.me/ip', timeout=10).read().decode().strip()
            return jsonify({'out': 'Внешний IP сервера: ' + ip})
        elif tool == 'dig':
            if not shutil.which('dig'):
                return jsonify({'error': 'нет dig: apt-get install -y dnsutils'}), 503
            p = subprocess.run(['dig', tgt, (cmd.strip() or 'A'), '+short'], capture_output=True, text=True, timeout=20)
        elif tool == 'dnsall':
            if not shutil.which('dig'):
                return jsonify({'error': 'нет dig: apt-get install -y dnsutils'}), 503
            outs = []
            for t in ('A', 'AAAA', 'MX', 'NS', 'TXT'):
                q = subprocess.run(['dig', tgt, t, '+short'], capture_output=True, text=True, timeout=20)
                outs.append('== ' + t + ' ==\\n' + (q.stdout or '(пусто)'))
            return jsonify({'out': '\\n'.join(outs)})
        elif tool == 'ptr':
            if not shutil.which('dig'):
                return jsonify({'error': 'нет dig: apt-get install -y dnsutils'}), 503
            p = subprocess.run(['dig', '-x', tgt, '+short'], capture_output=True, text=True, timeout=20)
        elif tool == 'ssl':
            port = int(d.get('port') or 443)
            if not shutil.which('openssl'):
                return jsonify({'error': 'на сервере нет openssl'}), 503
            q1 = subprocess.run(['openssl', 's_client', '-connect', tgt + ':' + str(port), '-servername', tgt],
                                capture_output=True, text=True, timeout=20, input='')
            q2 = subprocess.run(['openssl', 'x509', '-noout', '-dates', '-subject', '-issuer'],
                                capture_output=True, text=True, timeout=20, input=q1.stdout)
            return jsonify({'out': q2.stdout or q1.stderr[:500]})
        elif tool == 'rkn':
            import urllib.request as _ur
            import json as _json
            is_ip = set(tgt) <= set('0123456789.')
            url = ('https://api.reestr.rublacklist.net/v2/ip/' if is_ip else 'https://api.reestr.rublacklist.net/v2/domain/') + tgt + '/json'
            try:
                r = _ur.urlopen(url, timeout=15)
                data = _json.loads(r.read().decode())
                return jsonify({'out': 'НАЙДЕНО в реестре РКН: ' + _json.dumps(data, ensure_ascii=False)[:2000]})
            except Exception as e:
                if '404' in str(e):
                    return jsonify({'out': 'Не найдено в реестре РКН (цель: ' + tgt + ')'})
                return jsonify({'error': 'реестр РКН недоступен: ' + str(e)[:150]}), 503
        elif tool == 'httphead':
            p = subprocess.run(['curl', '-sI', '-m', '10', tgt if tgt.startswith('http') else ('http://' + tgt)],
                               capture_output=True, text=True, timeout=20)
        else:
            return jsonify({'error': 'неизвестный инструмент'}), 400""",
    'эндпоинт: новые инструменты')

# 2) Новые пункты в селекте Тулзы
rep('<option value="curl">HTTP/RTSP проверка (curl)</option>',
"""<option value="curl">HTTP/RTSP проверка (curl)</option>
<option value="whois">WHOIS (владелец домена/IP)</option>
<option value="myip">Мой внешний IP (сервер)</option>
<option value="dig">DIG (тип записи в поле «Текст»: A/MX/NS/TXT)</option>
<option value="dnsall">Все DNS-записи (A/AAAA/MX/NS/TXT)</option>
<option value="ptr">PTR (обратная запись IP)</option>
<option value="ssl">SSL-сертификат (сроки/владелец, порт 443)</option>
<option value="rkn">Реестр РКН (домен/IP)</option>
<option value="httphead">HTTP-заголовки сайта (curl -I)</option>""",
    'селект: новые инструменты')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')