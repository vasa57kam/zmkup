import ast, os
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

def slice_replace(text, start_marker, end_marker, new_body, label):
    i = text.find(start_marker)
    if i < 0:
        print('  ПРОПУСК (старт):', label); return text
    j = text.find(end_marker, i + len(start_marker))
    if j < 0:
        print('  ПРОПУСК (конец):', label); return text
    print('  ok:', label)
    return text[:i] + new_body + text[j+len(end_marker):]

# 1) Карточка камеры и saveCam — целиком, с логином/паролем/RTSP/портом/VLAN и файлами
ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
NEW_CARD = '''function camCard(c){
  var side=c.side==='old'?'СТАРНАЯ':'НОВАЯ';
  return '<div style="border:1px solid #ddd;border-radius:8px;padding:.8rem;margin:.5rem 0;" data-cam="'+c.id+'">'
   +'<b>📹 '+side+' камера</b> '
   +'<button class="btn btn-danger" style="padding:2px 8px;" onclick="delCam('+c.id+')">🗑</button>'
   +'<div class="form-row">'
   +'<div class="form-group"><label>Модель:</label><input class="camModel" value="'+(c.model||'')+'" placeholder="Beward BR-2.4 и т.п."></div>'
   +'<div class="form-group"><label>Серийник:</label><input class="camSerial" value="'+(c.serial||'')+'"></div>'
   +'<div class="form-group"><label>IP / ID:</label><input class="camIp" value="'+(c.ip||'')+'"></div>'
   +'</div>'
   +'<div class="form-row">'
   +'<div class="form-group"><label>Логин:</label><input class="camLogin" value="'+(c.login||'')+'" placeholder="br-291095"></div>'
   +'<div class="form-group"><label>Пароль:</label><input class="camPass" value="'+(c.password||'')+'"></div>'
   +'<div class="form-group"><label>MAC:</label><input class="camMac" value="'+(c.mac||'')+'"></div>'
   +'</div>'
   +'<div class="form-row">'
   +'<div class="form-group"><label>Порт / VLAN:</label><input class="camPort" style="width:60px;" value="'+(c.port||'')+'" placeholder="21"> / <input class="camVlan" style="width:60px;" value="'+(c.vlan||'')+'" placeholder="135"></div>'
   +'<div class="form-group"><label>Зона / надпись:</label><input class="camZone" value="'+(c.zone||'')+'"></div>'
   +'</div>'
   +'<div class="form-group"><label>RTSP-поток:</label><input class="camRtsp" value="'+(c.rtsp||'')+'" placeholder="rtsp://admin:pass@ip:554/av0_0"></div>'
   +'<div class="form-group"><label>Примечания:</label><input class="camNotes" value="'+(c.notes||'')+'"></div>'
   +'<div class="form-group"><label>Конфиг (экспорт/импорт):</label><textarea class="camCfg" style="width:100%;height:90px;font-family:monospace;">'+(c.config_text||'')+'</textarea></div>'
   +'<button class="btn btn-primary" onclick="saveCam('+c.id+')">💾 Сохранить</button> '
   +'<button class="btn btn-secondary" onclick="exportCam('+c.id+')">📤 Экспорт конфига</button> '
   +'<button class="btn btn-secondary" onclick="importCam('+c.id+')">📥 Импорт конфига</button>'
   +'<div class="form-group" style="margin-top:.5rem;"><label>Файлы камеры (конфиг, бэкап, фото шильдика):</label>'
   +'<div id="camFiles_'+c.id+'"></div>'
   +'<input type="file" onchange="uploadAttachment(\\'camera\\','+c.id+',\\'camFiles_'+c.id+'\\',this)"></div>'
   +'</div>';
}
'''
NEW_SAVE = '''function saveCam(id){
  var d=document.querySelector('[data-cam="'+id+'"]');
  var body={model:d.querySelector('.camModel').value, serial:d.querySelector('.camSerial').value,
    ip:d.querySelector('.camIp').value, mac:d.querySelector('.camMac').value,
    zone:d.querySelector('.camZone').value, notes:d.querySelector('.camNotes').value,
    login:d.querySelector('.camLogin').value, password:d.querySelector('.camPass').value,
    rtsp:d.querySelector('.camRtsp').value, vlan:d.querySelector('.camVlan').value,
    port:d.querySelector('.camPort').value,
    config_text:d.querySelector('.camCfg').value};
  fetch('/api/cameras/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(){alert('Сохранено');});
}
'''
if 'camLogin' not in ajs or 'camFiles_' not in ajs:
    ajs = slice_replace(ajs, 'function camCard(c){', '\n}\n', NEW_CARD, 'camCard целиком')
    ajs = slice_replace(ajs, 'function saveCam(id){', '\n}\n', NEW_SAVE, 'saveCam целиком')
    open(ajs_path, 'w').write(ajs)
    print('ok: common.js переписан')
else:
    print('common.js уже полный')

# 2) want_patch: строгий повтор в do_ai, если патч обязателен
rep("    JOB['result'] = {'ok': True, 'rc': 0, 'out': text[:8000]}",
"""    if (payload or {}).get('want_patch') and not _extract_patch(text).strip():
        job_log('[ai] патча нет при want_patch — строгий повтор...')
        text = _ollama_gen(prompt + '\\n\\nВАЖНО: ты ОБЯЗАН выдать готовый ИСПОЛНЯЕМЫЙ python-патч между ===PATCH=== и ===END=== (читает swh.py, правит через replace с точными якорями, пишет обратно, ast.parse). Формат git diff ЗАПРЕЩЁН. Пояснения — после патча, кратко.', 16384, 900)
    JOB['result'] = {'ok': True, 'rc': 0, 'out': text[:8000]}""", 'want_patch строгий повтор')

rep("startJob('ai',{prompt:p, with_diag:true, attach:a});",
    "startJob('ai',{prompt:p, with_diag:true, attach:a, want_patch:1});", 'кнопки требуют патч')

# 3) Режим камеры: переименовать заголовки формы
rep("""  var uw=document.getElementById('uplinksWrap');
  if(uw){ uw.style.display=cam?'none':''; }
}""",
"""  var uw=document.getElementById('uplinksWrap');
  if(uw){ uw.style.display=cam?'none':''; }
  var hs=document.querySelectorAll('#createOrderModal h3');
  if(hs.length>=2){
    if(cam){ hs[0].textContent='Старая камера (адрес, подъезд)'; hs[1].textContent='Новая камера'; }
    else { hs[0].textContent='Старый коммутатор'; hs[1].textContent='Новый коммутатор'; }
  }
}""", 'заголовки камера/коммутатор')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')