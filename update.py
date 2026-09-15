import ast, os
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) openDevTools в common.js
ajs_path = os.path.join('static', 'common.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'openDevTools' not in ajs:
    ajs += '''
function openDevTools(s){
  if(!s){ alert('Устройство не указано'); return; }
  var ip=(s.match(/(\\d{1,3}\\.){3}\\d{1,3}/)||[null])[0];
  if(!ip && window.devArr){
    var d=devArr.find(function(x){ return x.name===s; });
    if(d){ ip=d.ip_address; }
  }
  if(!ip){ alert('Не найден IP устройства: '+s); return; }
  sessionStorage.setItem('toolz_tgt', ip);
  sessionStorage.setItem('toolz_tool', 'ssh');
  location.href='/tools';
}
'''
    open(ajs_path, 'w').write(ajs)
    print('ok: openDevTools')

# 2) Планировщик: uplink-таблица — select устройств + адрес + 🔗
rep("""<tr data-lid="${link.id}">
                                <td><input type="number" class="port-input" value="${link.old_port}" onchange="updLink(${link.id}, 'old_port', this.value)"></td>
                                <td><input type="text" class="port-input" style="width:160px;" value="${link.upstream_device||''}" onchange="updLink(${link.id}, 'upstream_device', this.value)"></td>
                                <td><input type="number" class="port-input" value="${link.upstream_port||''}" onchange="updLink(${link.id}, 'upstream_port', this.value)"></td>""",
"""<tr data-lid="${link.id}">
                                <td><input type="number" class="port-input" value="${link.old_port}" onchange="updLink(${link.id}, 'old_port', this.value)"></td>
                                <td><select class="port-input devsel" data-cur="${link.upstream_device||''}" onchange="updLink(${link.id}, 'upstream_device', this.value)"></select></td>
                                <td>${devLocSync(link.upstream_device)?'📍 '+devLocSync(link.upstream_device):''} <a href="#" data-dev="${link.upstream_device||''}" onclick="openDevTools(this.dataset.dev);return false;">🔗</a></td>
                                <td><input type="number" class="port-input" value="${link.upstream_port||''}" onchange="updLink(${link.id}, 'upstream_port', this.value)"></td>""",
    'uplink: select + адрес')

rep('<thead><tr><th>Порт</th><th>Устройство</th><th>Порт устройства</th><th></th></tr></thead>',
    '<thead><tr><th>Порт</th><th>Устройство</th><th>Адрес</th><th>Порт устройства</th><th></th></tr></thead>',
    'uplink: шапка с адресом')

# 3) Планировщик: downlink-таблица — select устройств + адрес + 🔗
rep("""<tr>
                                <td><input type="number" class="port-input" value="${link.old_port}" onchange="updLink(${link.id}, 'old_port', this.value)"></td>
                                <td><input type="text" class="port-input" style="width:160px;" value="${link.upstream_device||''}" onchange="updLink(${link.id}, 'upstream_device', this.value)"></td>
                                <td><input type="number" class="port-input" value="${link.upstream_port||''}" onchange="updLink(${link.id}, 'upstream_port', this.value)"></td>
                                <td><input type="number" class="port-input" value="${link.new_port||''}" onchange="updLink(${link.id}, 'new_port', this.value)"></td>""",
"""<tr>
                                <td><input type="number" class="port-input" value="${link.old_port}" onchange="updLink(${link.id}, 'old_port', this.value)"></td>
                                <td><select class="port-input devsel" data-cur="${link.upstream_device||''}" onchange="updLink(${link.id}, 'upstream_device', this.value)"></select></td>
                                <td>${devLocSync(link.upstream_device)?'📍 '+devLocSync(link.upstream_device):''} <a href="#" data-dev="${link.upstream_device||''}" onclick="openDevTools(this.dataset.dev);return false;">🔗</a></td>
                                <td><input type="number" class="port-input" value="${link.upstream_port||''}" onchange="updLink(${link.id}, 'upstream_port', this.value)"></td>
                                <td><input type="number" class="port-input" value="${link.new_port||''}" onchange="updLink(${link.id}, 'new_port', this.value)"></td>""",
    'downlink: select + адрес')

rep('<thead><tr><th>Порт</th><th>Устройство</th><th>Порт устройства</th><th>Новый порт</th><th></th></tr></thead>',
    '<thead><tr><th>Порт</th><th>Устройство</th><th>Адрес</th><th>Порт устройства</th><th>Новый порт</th><th></th></tr></thead>',
    'downlink: шапка с адресом')

# 4) Наполнение селектов после отрисовки таблиц
rep('    renderReminders(order, links);',
"""    document.querySelectorAll('.devsel').forEach(function(sel){
      fillDevSelect(sel, sel.dataset.cur||'');
    });
    renderReminders(order, links);""", 'наполнение devsel')

# 5) Тулза: приём цели со страницы планировщика
if 'toolz_tgt' not in src:
    rep('function pin(){',
"""var _t=sessionStorage.getItem('toolz_tgt');
if(_t){
  sessionStorage.removeItem('toolz_tgt');
  var _tt=sessionStorage.getItem('toolz_tool');
  if(_tt){ sessionStorage.removeItem('toolz_tool'); }
  window.addEventListener('DOMContentLoaded', function(){
    document.getElementById('tgt').value=_t;
    if(_tt){ document.getElementById('tool').value=_tt; }
  });
}
function pin(){""", 'tools: приём цели')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')