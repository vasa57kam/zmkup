import ast, sqlite3
src = open('swh.py').read()

# 1) Статья в базу знаний (создаётся один раз)
conn = sqlite3.connect('switch_replacements.db')
conn.execute('''CREATE TABLE IF NOT EXISTS kb_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT, category TEXT, tags TEXT, body TEXT, schema TEXT, created_at TEXT)''')
row = conn.execute("SELECT id FROM kb_articles WHERE title LIKE '%магистраль%абонент%ISM%' OR title LIKE '%ISM/IGMP%'").fetchone()
if not row:
    from datetime import datetime
    BODY = '''ПОРЯДОК ПЕРЕВОДА МАГИСТРАЛЬНОГО ПОРТА В АБОНЕНТСКИЙ НА DES-3200 (и любых свитчах с ISM/IGMP snooping multicast_vlan, IPTV vlan 1151):

0) Посмотреть текущую конфигурацию ISM:
   show igmp_snooping multicast_vlan vlan1151
   Роли портов: source_port — куда заходит поток (напр. 27); tag_member_port — магистрали (напр. 25); member_port — абонентские (1-24,26,28).

1) ЕСЛИ переводимый порт является source_port — СНАЧАЛА назначить source_port новому порту, и только потом убирать старый. Иначе ошибка:
   "wrong ISM config (see limits also) Source is absent should be 27. The configuration was corrected automatically"
   (свитч сам перекроил конфиг, multicast мог отвалиться).

2) Убрать порт из tag_member_port:
   config igmp_snooping multicast_vlan vlan1151 delete tag_member_port 25
3) Добавить порт в member_port (теперь он абонентский):
   config igmp_snooping multicast_vlan vlan1151 add member_port 25
4) ТОЛЬКО ТЕПЕРЬ менять VLAN-ы: убрать порт из магистрального VLAN (config vlan vlanid N delete 25), добавить untagged в абонентский + pvid.
5) save. Проверить: show igmp_snooping multicast_vlan vlan1151, IPTV у абонентов, show log.

ПРИМЕР ЛОГА (2026-10-07, свитч 10.163.201.116 DES-3200-28):
config igmp_snooping multicast_vlan vlan1151 delete member_port 1-24,26,28
config igmp_snooping multicast_vlan vlan1151 delete tag_member_port 25,27
config igmp_snooping multicast_vlan vlan1151 add source_port 27
config igmp_snooping multicast_vlan vlan1151 add member_port 1-24,26,28
config igmp_snooping multicast_vlan vlan1151 add tag_member_port 25

ВЫВОД: сначала разбираемся с ролями ISM (source/tag_member/member), потом трогаем VLAN-ы. Нарушение порядка = автоисправление конфига свитчом + риск потери multicast + злой глав инженер.'''
    conn.execute('INSERT INTO kb_articles (title, category, tags, body, schema, created_at) VALUES (?,?,?,?,?,?)',
                 ('DES-3200: перевод магистрального порта в абонентский без ошибок ISM/IGMP (vlan1151)',
                  'Свитчи', 'IGMP, ISM, multicast_vlan, vlan1151, DES-3200, IPTV, tag_member_port, source_port',
                  BODY, '', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    print('ok: статья БЗ создана')
else:
    print('статья БЗ уже есть')
conn.close()

# 2) Операции ISM + комбо в генераторе (семейство DES)
p = 'static/gen.js'
js = open(p).read()
def rj(old, new, label):
    global js
    if old in js:
        js = js.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

rj(" ddm_all:'show ddm'\n},\ndgs:{",
   " ddm_all:'show ddm',\n ism_show:'show igmp_snooping multicast_vlan vlan{vlan}',\n ism_del_tag:'config igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {ports}',\n ism_del_mem:'config igmp_snooping multicast_vlan vlan{vlan} delete member_port {ports}',\n ism_add_mem:'config igmp_snooping multicast_vlan vlan{vlan} add member_port {ports}',\n ism_add_src:'config igmp_snooping multicast_vlan vlan{vlan} add source_port {ports}',\n t2a:'config igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {ports}\\nconfig igmp_snooping multicast_vlan vlan{vlan} add member_port {ports}\\nconfig vlan vlanid {trunk} delete {ports}\\nconfig vlan vlanid {text} add untagged {ports}\\nconfig ports {ports} pvid {text}'\n},\ndgs:{",
   'TPL des: ISM + комбо t2a')

rj("ddm_all:'DDM всех портов (SFP)'};",
   "ddm_all:'DDM всех портов (SFP)',ism_show:'ISM: показать конфиг multicast_vlan (IPTV)',ism_del_tag:'ISM: убрать порт из tag_member (магистрали)',ism_del_mem:'ISM: убрать порт из member',ism_add_mem:'ISM: добавить порт в member (абонентский)',ism_add_src:'ISM: добавить source_port (куда заходит поток)',t2a:'КОМБО: магистраль→абонент без ошибок ISM'};",
   'NAMES: ISM')

rj("ddm_all:'Ничего вводить не надо.'};",
   "ddm_all:'Ничего вводить не надо.',ism_show:'VLAN — номер multicast-VLAN (обычно 1151). Покажет source_port / tag_member_port / member_port.',ism_del_tag:'VLAN=1151; Порт(ы) — магистральный порт, который переводим в абонентский.',ism_del_mem:'VLAN=1151; Порт(ы) — порты, убираемые из member.',ism_add_mem:'VLAN=1151; Порт(ы) — порты, ставшие абонентскими.',ism_add_src:'VLAN=1151; Порт(ы) — порт, куда заходит IPTV-поток (напр. 27). БЕЗ source будет ошибка «Source is absent».',t2a:'VLAN=1151 (multicast); Порт(ы) — переводимый порт; Порт(ы) магистрали — его СТАРЫЙ магистральный VLAN; Текст — НОВЫЙ абонентский VLAN. Даёт 5 команд правильным порядком.'};",
   'HINTS: ISM')

rj("ddm:'1) Tx/Rx мощность\\n2) Rx ниже -25 dBm — деградация оптики\\n3) почистить/заменить, снова сравнить'};",
   "ddm:'1) Tx/Rx мощность\\n2) Rx ниже -25 dBm — деградация оптики\\n3) почистить/заменить, снова сравнить',t2a:'1) show igmp_snooping multicast_vlan vlan1151 — посмотреть роли\\n2) если порт был source_port — СНАЧАЛА add source_port новому порту\\n3) delete tag_member_port, add member_port\\n4) убрать порт из магистрального VLAN\\n5) add untagged в абонентский + pvid\\n6) save\\n7) проверить IPTV у абонентов и show log (ошибка wrong ISM config = нет source)'};",
   'MEMO: t2a')

open(p, 'w').write(js)
print('ok: gen.js + ISM')

src = open('swh.py').read()
if '/static/gen.js?v=10' not in src:
    src = src.replace('/static/gen.js?v=9', '/static/gen.js?v=10', 1)
    print('ok: версия gen.js -> v10')
open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')