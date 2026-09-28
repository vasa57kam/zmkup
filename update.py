import ast, os
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Эндпоинт: файл вложения по ID (не зависит от имени файла)
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
    print('ok: /api/attachments/file/<id>')

# 2) Полевой режим: фото по ID
rep("""d.innerHTML=rows.map(function(a){ return '<a href="/uploads/'+a.filename+'" target="_blank"><img class="ph" src="/uploads/'+a.filename+'"></a>'; }).join('');""",
    """d.innerHTML=rows.map(function(a){ return '<a href="/api/attachments/file/'+a.id+'" target="_blank"><img class="ph" src="/api/attachments/file/'+a.id+'"></a>'; }).join('');""",
    'field: фото по ID')

# 3) common.js: миниатюры нарядов/камер по ID
ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if "'/uploads/'+a.filename" in ajs:
    ajs = ajs.replace("""d.innerHTML='<a href="/uploads/'+a.filename+'" target="_blank"><img src="/uploads/'+a.filename+'" style="width:120px;height:90px;object-fit:cover;border-radius:6px;"></a><br><small>'+(a.original_name||'')+'</small> <button onclick="delAtt('+a.id+',\\''+type+'\\','+id+',\\''+boxId+'\\')">🗑</button>';""",
"""d.innerHTML='<a href="/api/attachments/file/'+a.id+'" target="_blank"><img src="/api/attachments/file/'+a.id+'" style="width:120px;height:90px;object-fit:cover;border-radius:6px;"></a><br><small>'+(a.original_name||'')+'</small> <button onclick="delAtt('+a.id+',\\''+type+'\\','+id+',\\''+boxId+'\\')">🗑</button>';""", 1)
    open(ajs_path, 'w').write(ajs)
    print('ok: common.js по ID')
else:
    print('common.js уже по ID или якорь иной')

# 4) kb.js: картинки статей по ID
kjs_path = os.path.join('static', 'kb.js')
kjs = open(kjs_path).read() if os.path.exists(kjs_path) else ''
if "'/uploads/'+x.filename" in kjs:
    kjs = kjs.replace("""'<span style="display:inline-block;margin:6px;text-align:center;"><a href="/uploads/'+x.filename+'" target="_blank"><img src="/uploads/'+x.filename+'" style="width:160px;height:115px;object-fit:cover;border-radius:6px;"></a><br><small>'+esc(x.original_name||'')+'</small> <button class="noprint" onclick="delKbImg('+x.id+')">🗑</button></span>'""",
"""'<span style="display:inline-block;margin:6px;text-align:center;"><a href="/api/attachments/file/'+x.id+'" target="_blank"><img src="/api/attachments/file/'+x.id+'" style="width:160px;height:115px;object-fit:cover;border-radius:6px;"></a><br><small>'+esc(x.original_name||'')+'</small> <button class="noprint" onclick="delKbImg('+x.id+')">🗑</button></span>'""", 1)
    open(kjs_path, 'w').write(kjs)
    print('ok: kb.js по ID')
else:
    print('kb.js уже по ID или якорь иной')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')