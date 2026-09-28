import ast, os, re
src = open('swh.py').read()
def rep(old, new, label, all_=False):
    global src
    if old in src:
        src = src.replace(old, new) if all_ else src.replace(old, new, 1)
        print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Маршрут /uploads/... гарантированно
if "'/uploads/<path:filename>'" not in src:
    ep = '''
@app.route('/uploads/<path:filename>')
def uploads_serve(filename):
    return send_from_directory(UPLOAD_DIR, filename)


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    print('ok: маршрут /uploads')

# 2) Отдача по ID гарантированно
if "'/api/attachments/file/" not in src:
    ep = '''
@app.route('/api/attachments/file/<int:att_id>')
def attachment_file(att_id):
    conn = get_db()
    r = conn.execute('SELECT filename FROM attachments WHERE id=?', (att_id,)).fetchone()
    conn.close()
    if not r:
        return 'Файл не найден', 404
    return send_from_directory(UPLOAD_DIR, r['filename'])


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    print('ok: отдача по ID')

# 3) Жёсткая проверка записи при загрузке
m = re.search(r"([ \t]*)(\w+)\.save\(os\.path\.join\(UPLOAD_DIR, *(\w+)\)\)", src)
if m:
    ind, obj, var = m.groups()
    new = (ind + "os.makedirs(UPLOAD_DIR, exist_ok=True)\n"
           + ind + obj + ".save(os.path.join(UPLOAD_DIR, " + var + "))\n"
           + ind + "if not os.path.exists(os.path.join(UPLOAD_DIR, " + var + ")):\n"
           + ind + "    return jsonify({'error': 'файл не записался на диск (место/права?)'}), 500\n")
    src = src[:m.start()] + new + src[m.end():]
    print('ok: проверка записи файла')
else:
    print('ПРОПУСК: строка save() не найдена')

# 4) Диагностика файлов-призраков
if 'def _missing_files' not in src:
    helper = '''
def _missing_files():
    try:
        conn = get_db()
        rows = conn.execute('SELECT id, filename FROM attachments').fetchall()
        conn.close()
        return [r['id'] for r in rows if not os.path.exists(os.path.join(UPLOAD_DIR, r['filename']))]
    except Exception:
        return [-1]

@app.route('/api/admin/files_check')
def files_check():
    if request.args.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    conn = get_db()
    rows = conn.execute('SELECT id, filename, original_name FROM attachments').fetchall()
    conn.close()
    missing = [{'id': r['id'], 'filename': r['filename'], 'original': r['original_name']}
               for r in rows if not os.path.exists(os.path.join(UPLOAD_DIR, r['filename']))]
    return jsonify({'missing': missing, 'uploads_dir': UPLOAD_DIR,
                    'dir_exists': os.path.isdir(UPLOAD_DIR),
                    'sample': (sorted(os.listdir(UPLOAD_DIR))[:20] if os.path.isdir(UPLOAD_DIR) else [])})

'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + helper + src[idx:]
    print('ok: _missing_files + /api/admin/files_check')

if "'files_missing'" not in src:
    rep("'vlans_count': _vlans_count(),",
        "'vlans_count': _vlans_count(),\n            'files_missing': _missing_files(),",
        'диагностика: files_missing')

# 5) Все ссылки на картинки — по ID (во всех файлах)
rep("'/uploads/'+a.filename+'", "'/api/attachments/file/'+a.id+'", 'swh: ссылки по ID', all_=True)
rep("'/uploads/'+x.filename+'", "'/api/attachments/file/'+x.id+'", 'swh: ссылки по ID (x)', all_=True)
for fn in ('static/common.js', 'static/kb.js'):
    if os.path.exists(fn):
        t = open(fn).read()
        o = t
        t = t.replace("'/uploads/'+a.filename+'", "'/api/attachments/file/'+a.id+'")
        t = t.replace("'/uploads/'+x.filename+'", "'/api/attachments/file/'+x.id+'")
        if t != o:
            open(fn, 'w').write(t)
            print('ok:', fn, '-> по ID')

# 6) Показ файлов-призраков в админке
ajs_path = os.path.join('static', 'admin.js')
if os.path.exists(ajs_path):
    ajs = open(ajs_path).read()
    if 'Файлов-призраков' not in ajs:
        ajs = ajs.replace("    L.push('VLANов в БД: '",
"""    L.push('Файлов-призраков (нет на диске): '+((res.files_missing||[]).length? ('ID '+(res.files_missing||[]).join(', ')+' — удалите эти вложения и залейте заново') : '0'));
    L.push('VLANов в БД: '""", 1)
        open(ajs_path, 'w').write(ajs)
        print('ok: admin.js показывает призраков')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')