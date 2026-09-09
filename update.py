import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Хелперы адресов в базовый скрипт (если не встали)
if 'function devLocSync' not in src:
    rep("    <script>\n    async function loadAttachments",
"""    <script>
    window.devArr=[];
    function devList(){
      if(!window.devCache){
        window.devCache=fetch('/api/network-map').then(function(r){return r.json();}).then(function(ds){ window.devArr=ds; return ds; });
      }
      return window.devCache;
    }
    function devLocSync(s){
      if(!s||!window.devArr){ return ''; }
      for(var i=0;i<window.devArr.length;i++){
        var d=window.devArr[i];
        if(d.name && s.indexOf(d.name)>=0){ return d.location||''; }
        if(d.ip_address && s.indexOf(d.ip_address)>=0){ return d.location||''; }
      }
      return '';
    }
    devList();
    async function loadAttachments""", 'хелперы адресов')

# 2) Предохранители в планировщике и на главной
rep('function loadSubscribers() {',
"""if(typeof devLocSync==='undefined'){ window.devLocSync=function(){ return ''; }; }
if(typeof devList==='undefined'){ window.devList=function(){ return Promise.resolve([]); }; }
function loadSubscribers() {""", 'предохранитель планировщика')

rep('let uplinkCount = 0;',
"""if(typeof devList==='undefined'){ window.devList=function(){ return Promise.resolve([]); }; }
if(typeof devLocSync==='undefined'){ window.devLocSync=function(){ return ''; }; }
let uplinkCount = 0;""", 'предохранитель главной')

# 3) Паспорт в планировщике и на наряде
if 'href="/passport/' not in src:
    rep('<button class="btn btn-success" onclick="exportReport()">',
        '<a class="btn btn-secondary" href="/passport/{{ order_id }}" target="_blank">🖨️ Паспорт</a>\n        <button class="btn btn-success" onclick="exportReport()">',
        'паспорт в планировщике')
if "a1b.href='/passport/'" not in src:
    rep('ha.appendChild(a1);',
"""ha.appendChild(a1);
    var a1b=document.createElement('a');
    a1b.className='btn btn-secondary';
    a1b.target='_blank';
    a1b.href='/passport/'+orderId;
    a1b.textContent='🖨️ Паспорт';
    ha.appendChild(a1b);""", 'паспорт на наряде')

# 4) САМОПОЧИНКА БОЛЬШЕ НЕ ПРИМЕНЯЕТ САМА — только готовит патч
rep("""    job_log('[selfheal] применяю патч нейронки...')
    rc, out = _run_patch_code(code, 'selfheal')
    JOB['result'] = {'ok': rc == 0, 'rc': rc, 'out': out[-4000:], 'ai': text[:1500]}
    if rc == 0:
        job_log('[selfheal] применено, перезапуск...')
        _restart_later()
    else:
        job_log('[selfheal] НЕ применён, rc=' + str(rc))""",
"""    job_log('[selfheal] патч ГОТОВ — примените кнопкой ⚡ после просмотра')
    JOB['result'] = {'ok': True, 'rc': 0,
        'out': 'Самопочинка подготовила патч, но НЕ применила его. Просмотрите ответ и нажмите ⚡ Применить предложенный патч (или пришлите ответ мастеру на проверку).',
        'ai': text[:6000]}""", 'самопочинка: безопасный режим')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')