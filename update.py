import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Планировщик: обёртка блока абонентов (чтобы скрывать при новой установке)
rep('<h3>👥 Абоненты (необязательно, для FDB-сравнения)</h3>',
    '<div id="subsBlock">\n<h3>👥 Абоненты (необязательно)</h3>',
    'обёртка: начало блока абонентов')

rep('<button class="btn btn-primary" onclick="showAddSubscriberModal()">+ Добавить абонента</button>',
    '<button class="btn btn-primary" id="addSubBtn" onclick="showAddSubscriberModal()">+ Добавить абонента</button>\n</div>',
    'обёртка: конец блока абонентов')

# 2) Хук: при загрузке наряда в планировщике включаем режим установки
rep("""        .then(order => {
            document.getElementById('oldSwitchInfo').innerHTML = `""",
"""        .then(order => {
            window.orderType=order.order_type||'replace';
            applyNewMode(order);
            document.getElementById('oldSwitchInfo').innerHTML = `""",
    'хук: режим установки в планировщике')

# 3) Функции режима установки (одноразово)
if 'function applyNewMode' not in src:
    rep('function renderReminders(order, links){',
"""function applyNewMode(order){
  if((order.order_type||'replace')!=='new') return;
  var oc=document.getElementById('oldSwitchInfo');
  if(oc){ var c=oc.closest('.info-card'); if(c){ c.style.display='none'; } }
  var sb=document.getElementById('subsBlock');
  if(sb){ sb.style.display='none'; }
  var ab=document.getElementById('addSubBtn');
  if(ab){ ab.style.display='none'; }
  var h=document.querySelector('.page-header h1');
  if(h){ h.textContent='🗺️ Планировщик установки — наряд №'+(order.order_number||''); }
}
function renderNewReminders(order, ups, dls){
  var h='';
  ups.forEach(function(l){
    h+='<li>На <b>'+(l.upstream_device||'?')+'</b> порт '+(l.upstream_port||'?')+': настроить uplink на НОВЫЙ свитч <b>'+order.new_switch_ip+'</b> порт <b>'+(l.new_port||l.old_port||'??')+'</b></li>';
  });
  dls.forEach(function(l){
    h+='<li>На <b>'+(l.upstream_device||'?')+'</b> порт '+(l.upstream_port||'?')+': настроить линк на НОВЫЙ свитч <b>'+order.new_switch_ip+'</b> порт <b>'+(l.new_port||'?? — назначьте выше!')+'</b></li>';
  });
  h+='<li>Завести карточку нового свитча в базе: адрес <b>'+(order.new_switch_location||'—')+'</b>, модель '+(order.new_switch_model||'')+', фото узла.</li>';
  h+='<li>Занести FDB нового свитча (кнопка «ПОСЛЕ замены») для истории.</li>';
  h+='<li>Добавить новый свитч на карту сети с адресом установки.</li>';
  return h;
}
function renderReminders(order, links){""",
        'функции: applyNewMode + renderNewReminders')

# 4) Напоминания: ветка для новой установки
rep("""    const dls=links.filter(l=>l.link_type==='downlink');
    let html='<ul style="margin-left:1.2rem;line-height:1.7;">';""",
"""    const dls=links.filter(l=>l.link_type==='downlink');
    if((order.order_type||'replace')==='new'){
      document.getElementById('reminders').innerHTML='<ul style="margin-left:1.2rem;line-height:1.7;">'+renderNewReminders(order, ups, dls)+'</ul>';
      return;
    }
    let html='<ul style="margin-left:1.2rem;line-height:1.7;">';""",
    'напоминания: ветка новой установки')

# 5) Карта наряда: для новой установки только «КАК СТАНЕТ»
rep("""    document.getElementById('orderMap').innerHTML =
        diagram('КАК БЫЛО (старый '+order.old_switch_ip+')', order.old_switch_ip, order.old_switch_model, l=>l.old_port) +
        '<hr style="margin:1rem 0;">' +
        diagram('КАК СТАНЕТ (новый '+order.new_switch_ip+')', order.new_switch_ip, order.new_switch_model, l=>l.new_port||l.old_port);""",
"""    var mapHtml='';
    if((order.order_type||'replace')!=='new'){
        mapHtml+=diagram('КАК БЫЛО (старый '+order.old_switch_ip+')', order.old_switch_ip, order.old_switch_model, l=>l.old_port) +
        '<hr style="margin:1rem 0;">';
    }
    mapHtml+=diagram('КАК СТАНЕТ (новый '+order.new_switch_ip+')', order.new_switch_ip, order.new_switch_model, l=>l.new_port||l.old_port);
    document.getElementById('orderMap').innerHTML=mapHtml;""",
    'карта: только КАК СТАНЕТ для установки')

# 6) Страница наряда: при новой установке старый свитч = «отсутствует»
i = src.find("fetch(`/api/links/${orderId}`)")
if i > 0 and 'отсутствует (новая установка)' not in src[max(0, i-800):i]:
    ins = """fetch('/api/orders/'+orderId).then(function(r){return r.json();}).then(function(o){
      if(o.order_type==='new'){
        var cds=document.querySelectorAll('#orderDetails .info-card');
        if(cds[0]){ cds[0].innerHTML='<h4>Старый коммутатор</h4><p>— отсутствует (новая установка)</p>'; }
      }
    });
    """
    src = src[:i] + ins + src[i:]
    print('  ok: страница наряда без старого (безопасная вставка)')
else:
    print('  пропуск: страница наряда (уже сделано или якорь не найден)')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')