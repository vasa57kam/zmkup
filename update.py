import ast
p = 'static/gen.js'
js = open(p).read()
def rj(old, new, label):
    global js
    if old in js:
        js = js.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) DES: комбо камеры = create + tagged магистрали + untagged камера + pvid + save
rj(" cam:'create vlan {text} tag {vlan}\\nconfig vlan vlanid {vlan} add untagged {ports}\\nconfig ports {ports} pvid {vlan}',",
   " cam:'create vlan {text} tag {vlan}\\nconfig vlan vlanid {vlan} add tagged {trunk}\\nconfig vlan vlanid {vlan} add untagged {ports}\\nconfig ports {ports} pvid {vlan}\\nsave',",
   'DES cam: + магистрали')

# 2) DES: транзит на магистрали использует поле {trunk}
rj(" trunk:'config vlan vlanid {vlan} add tagged {ports}',",
   " trunk:'config vlan vlanid {vlan} add tagged {trunk}',",
   'DES trunk: {trunk}')

# 3) DGS: комбо камеры с магистральным интерфейсом
rj(" cam:'vlan database\\nvlan {vlan}\\nexit\\ninterface ethernet 1/0/{ports}\\nvlan participation include {vlan}\\nvlan pvid {vlan}\\nexit',",
   " cam:'vlan database\\nvlan {vlan}\\nexit\\ninterface ethernet 1/0/{trunk}\\nvlan participation include {vlan}\\nvlan tagging tagged\\nexit\\ninterface ethernet 1/0/{ports}\\nvlan participation include {vlan}\\nvlan pvid {vlan}\\nexit\\ncopy running-config startup-config',",
   'DGS cam: + магистрали')

# 4) DGS: транзит
rj(" trunk:'interface ethernet 1/0/{ports}\\nvlan participation include {vlan}\\nvlan tagging tagged\\nexit'",
   " trunk:'interface ethernet 1/0/{trunk}\\nvlan participation include {vlan}\\nvlan tagging tagged\\nexit'",
   'DGS trunk: {trunk}')

# 5) gen(): подстановка {trunk}
rj(".replace(/{ports}/g,document.getElementById('p').value)",
   ".replace(/{ports}/g,document.getElementById('p').value)\n         .replace(/{trunk}/g,(document.getElementById('tr')||{}).value||'')",
   'gen: {trunk}')

# 6) Подсказки и названия
rj("cam:'Текст (DES) — ИМЯ VLAN; VLAN — номер; Порт(ы) — порт камеры. Даёт полный набор команд.',",
   "cam:'Текст — ИМЯ VLAN (напр. OTS.INTERCOM.UFA.PRV); VLAN — номер (135); Порт(ы) магистрали — транк-порты (tagged, напр. 26-28); Порт(ы) — порт камеры (untagged+pvid). Даёт весь набор по инструкции + save.',",
   'HINTS cam')
rj("trunk:'VLAN — номер; Порт(ы) — магистральный порт на ядро.',",
   "trunk:'VLAN — номер; Порт(ы) магистрали — ВСЕ транк-порты, куда прокидываем VLAN тегом (напр. 26-28 или 28). То самое «не забывать протранзировать!».',",
   'HINTS trunk')
rj("trunk:'КОМБО: магистраль на ядро (tagged)',",
   "trunk:'КОМБО: транзит VLAN на магистрали (tagged)',",
   'NAMES trunk')
rj("cam:'1) создать VLAN\\n2) добавить порт камеры untagged/participation\\n3) PVID порту\\n4) сохранить конфиг\\n5) в биллинге вписать VLAN (абон. и реал.)\\n6) проверить поток камеры',",
   "cam:'1) создать VLAN (имя + tag)\\n2) протранзить на магистрали tagged\\n3) добавить порт камеры untagged\\n4) PVID порту\\n5) save\\n6) в биллинге вписать VLAN (абон. и реал.)\\n7) проверить поток камеры',",
   'MEMO cam')

open(p, 'w').write(js)
print('ok: gen.js + магистрали')

src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 7) Поле «Порт(ы) магистрали» в форме
rep('Порт(ы): <input id="p" placeholder="21 или 26-28" style="width:120px;">',
    'Порт(ы): <input id="p" placeholder="21 или 16" style="width:110px;"> Порт(ы) магистрали: <input id="tr" placeholder="26-28 или 28" style="width:130px;">',
    'поле магистрали')

if '/static/gen.js?v=9' not in src:
    src = src.replace('/static/gen.js?v=8', '/static/gen.js?v=9', 1)
    print('ok: версия gen.js -> v9')
open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')