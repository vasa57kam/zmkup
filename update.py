import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Весь JS страницы /vlans — во внешний файл
PAGEJS = r'''var ROWS=[];
function norm(s){ return (s||'').toLowerCase().replace(/[^0-9a-zа-яё./-]/g,''); }
function baseRows(){
  var d=window.VLAN_DATA||[];
  return d.map(function(r){ return {region:r[0], switch_ip:r[1], segment:r[2], vlan:r[3]}; });
}
function mergeApi(cb){
  fetch('/api/vlans').then(function(r){return r.json();}).then(function(rows){
    (rows||[]).forEach(function(x){
      var ex=ROWS.some(function(r){ return r.region===x.region && String(r.vlan)===String(x.vlan); });
      if(!ex){ ROWS.push(x); }
    });
    if(cb){ cb(); }
    render();
  }).catch(function(){ if(cb){ cb(); } render(); });
}
function loadStatic(cb){
  var s=document.createElement('script');
  s.src='/static/vlans.js?ts='+Date.now();
  s.onload=function(){ cb(); };
  s.onerror=function(){ cb(); };
  document.head.appendChild(s);
}
function load(){
  var qp=new URLSearchParams(location.search).get('q')||'';
  if(qp){ document.getElementById('q').value=qp; }
  ROWS=baseRows();
  render();
  mergeApi(function(){
    if(ROWS.length===0){
      loadStatic(function(){ ROWS=baseRows(); mergeApi(null); });
    }
  });
}
function reloadVlans(){
  document.getElementById('cnt').textContent=' загружаю...';
  loadStatic(function(){ ROWS=baseRows(); mergeApi(null); });
}
function render(){
  var q=norm(document.getElementById('q').value);
  var f=ROWS.filter(function(r){
    if(!q) return true;
    return norm(r.region).indexOf(q)>=0 ||
           norm(r.segment).indexOf(q)>=0 ||
           norm(r.switch_ip).indexOf(q)>=0 ||
           String(r.vlan).indexOf(q)>=0;
  });
  document.getElementById('cnt').textContent=' всего: '+ROWS.length+', найдено: '+f.length;
  var w=document.getElementById('vwarn');
  if(w){ w.style.display=ROWS.length? 'none':'block'; }
  document.getElementById('tb').innerHTML=f.map(function(r){
    return '<tr><td>'+r.region+'</td><td>'+r.switch_ip+'</td><td>'+r.segment+'</td><td><b>'+r.vlan+'</b></td>'
      +'<td><button class="btn" style="background:#3498db;" onclick="navigator.clipboard.writeText(\''+r.vlan+'\');alert(\'VLAN скопирован\')">📋</button> '
      +'<button class="btn" style="background:#27ae60;" onclick="openSw(\''+r.switch_ip+'\')">🔗 свитч</button></td></tr>';
  }).join('');
}
function openSw(ip){
  sessionStorage.setItem('toolz_tgt', ip);
  sessionStorage.setItem('toolz_tool', 'ssh');
  location.href='/tools';
}
function impVlans(){
  var inp=document.getElementById('impFile');
  var f=inp.files[0];
  if(!f){ alert('Выберите файл xlsx или csv'); return; }
  var fd=new FormData();
  fd.append('file', f);
  fd.append('pin', localStorage.getItem('swhpin')||prompt('PIN:')||'');
  document.getElementById('impMsg').textContent='Импортирую...';
  fetch('/api/vlans/import',{method:'POST', body:fd}).then(function(r){return r.json();}).then(function(res){
    document.getElementById('impMsg').textContent=res.ok? ('Готово: добавлено '+res.added+', всего '+res.total) : ('Ошибка: '+(res.error||''));
    if(res.ok){ load(); }
  }).catch(function(e){ document.getElementById('impMsg').textContent='Ошибка: '+e.message; });
}
function addRow(){
  var b={region:document.getElementById('nReg').value, switch_ip:document.getElementById('nIp').value,
         segment:document.getElementById('nSeg').value, vlan:parseInt(document.getElementById('nVlan').value)||0,
         pin:localStorage.getItem('swhpin')||prompt('PIN:')||''};
  fetch('/api/vlans',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)})
  .then(function(r){return r.json();}).then(function(res){ if(res.ok){ load(); } else { alert('Ошибка: '+(res.error||'')); } });
}
if(document.readyState!=='loading'){ load(); }
else { document.addEventListener('DOMContentLoaded', load); }
'''
open('static/vlanspage.js', 'w').write(PAGEJS)
print('ok: static/vlanspage.js')

# 2) Страница /vlans: inline-скрипт заменяем внешним файлом
i = src.find('VLANS_HTML')
if i >= 0:
    a = src.find('<script>', i)
    b = src.find('</script>', a) if a >= 0 else -1
    if a >= 0 and b > a and 'vlanspage.js' not in src[a:b]:
        src = src[:a] + '<script src="/static/vlanspage.js?v=2"></script>\n<script>window.addEventListener("load",function(){ if(!window.impVlans){ var m=document.getElementById("impMsg"); if(m){ m.textContent="⚠️ JS страницы не загрузился — нажмите Ctrl+F5"; } } });</script>' + src[b+len('</script>'):]
        print('ok: /vlans на внешнем JS')
    else:
        print('скрипт уже внешний или якорь не найден')
else:
    print('ПРОПУСК: VLANS_HTML')

# 3) Кнопка импорта: защита от тишины
rep('onclick="impVlans()"',
    'onclick="if(window.impVlans){impVlans();}else{alert(\'JS страницы не загрузился — нажмите Ctrl+F5 и повторите\');}"',
    'кнопка импорта с защитой')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')