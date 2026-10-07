import ast, sqlite3
src = open('swh.py').read()

# 1) Дополняем статью БЗ: лимит одного source + безопасная смена source-порта
conn = sqlite3.connect('switch_replacements.db')
ADD = '''

=== ДОПОЛНЕНИЕ (2026-10): SOURCE-ПОРТ ISM ===
ВАЖНО: в одной ISM VLAN на DES-3200 может быть ТОЛЬКО ОДИН source_port (аппаратное ограничение).
Два источника нельзя: 1) петля мультикаст-трафика (положит CPU и полосу); 2) дублирование IPTV-каналов (рассыпается картинка).
Резервирование аплинков: LACP (объединить порты в trunk-группу и указать её как source_port) либо RSTP/ERPS (резервный порт блокируется протоколом, при падении основного открывается).

БЕЗОПАСНЫЙ ПОРЯДОК СМЕНЫ SOURCE-ПОРТА (старый S -> новый N):
1) config igmp_snooping multicast_vlan vlan<MV> delete member_port N      (если N был в клиентах)
2) config igmp_snooping multicast_vlan vlan<MV> delete tag_member_port N  (если N был тегированным)
3) config igmp_snooping multicast_vlan vlan<MV> delete source_port S
4) config igmp_snooping multicast_vlan vlan<MV> add source_port N
5) ФИЗИЧЕСКИ переставить патч-корд из S в N
6) config igmp_snooping multicast_vlan vlan<MV> add member_port S         (освободившийся старый порт — в клиенты)
7) show igmp_snooping multicast_vlan                                       (проверить роли)
8) show igmp_snooping group vlan vlan<MV>                                  (проверить группы/роутер-порт)
9) save
Примечание по синтаксису: на наших прошивках (лог 10.163.201.116) команда звучит как
"config igmp_snooping multicast_vlan vlan1151 ..."; в части гайдов/прошивок встречается
"config multicast_vlan vlan<N> ..." — суть та же, при ругани свитча менять префикс.'''
r = conn.execute("SELECT id FROM kb_articles WHERE title LIKE '%ISM/IGMP%' OR title LIKE '%магистраль%абонент%ISM%'").fetchone()
if r:
    conn.execute('UPDATE kb_articles SET body = body || ? WHERE id=?', (ADD, r[0]))
    conn.commit()
    print('ok: статья БЗ дополнена про source_port')
else:
    print('статья БЗ не найдена — создайте вручную или повторите прошлый update')
conn.close()

# 2) Генератор: операция безопасной смены source-порта
p = 'static/gen.js'
js = open(p).read()
def rj(old, new, label):
    global js
    if old in js:
        js = js.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

if 'ism_swap' not in js:
    rj(" t2a:'config igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {ports}",
       " ism_swap:'config igmp_snooping multicast_vlan vlan{vlan} delete member_port {trunk}\\nconfig igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {trunk}\\nconfig igmp_snooping multicast_vlan vlan{vlan} delete source_port {ports}\\nconfig igmp_snooping multicast_vlan vlan{vlan} add source_port {trunk}\\nconfig igmp_snooping multicast_vlan vlan{vlan} add member_port {ports}\\nshow igmp_snooping multicast_vlan\\nsave',\n t2a:'config igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {ports}",
       'TPL: ism_swap')
    rj("t2a:'КОМБО: магистраль→абонент без ошибок ISM'};",
       "t2a:'КОМБО: магистраль→абонент без ошибок ISM',ism_swap:'КОМБО: смена source-порта ISM (безопасный порядок)'};",
       'NAMES: ism_swap')
    rj("t2a:'VLAN — мультикаст-VLAN свитча (1151 или ваш); Порт(ы) — переводимый порт; Порт(ы) магистрали — его СТАРЫЙ магистральный VLAN; Текст — НОВЫЙ абонентский VLAN. 5 команд правильным порядком.'};",
       "t2a:'VLAN — мультикаст-VLAN свитча (1151 или ваш); Порт(ы) — переводимый порт; Порт(ы) магистрали — его СТАРЫЙ магистральный VLAN; Текст — НОВЫЙ абонентский VLAN. 5 команд правильным порядком.',ism_swap:'VLAN — мультикаст-VLAN; Порт(ы) — СТАРЫЙ source-порт (удаляемый); Порт(ы) магистрали — НОВЫЙ source-порт (добавляемый). Помни: source в ISM VLAN всегда ОДИН! Патч-корд переставить физически после назначения нового source.'};",
       'HINTS: ism_swap')
    rj("7) проверить IPTV и show log'};",
       "7) проверить IPTV и show log',ism_swap:'1) вычистить новый порт из member/tag_member\\n2) delete source_port старого\\n3) add source_port нового\\n4) ФИЗИЧЕСКИ переставить патч-корд\\n5) старый порт add member_port\\n6) show igmp_snooping multicast_vlan + group vlan\\n7) save\\n8) два source нельзя: петля мультикаста и дубли каналов; резерв — только LACP/RSTP/ERPS'};",
       'MEMO: ism_swap')
    open(p, 'w').write(js)
    print('ok: gen.js + ism_swap')
else:
    print('ism_swap уже есть')

src = open('swh.py').read()
if '/static/gen.js?v=12' not in src:
    src = src.replace('/static/gen.js?v=11', '/static/gen.js?v=12', 1)
    print('ok: версия gen.js -> v12')
open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')