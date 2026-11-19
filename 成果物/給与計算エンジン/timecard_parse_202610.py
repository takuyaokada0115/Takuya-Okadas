#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re, unicodedata

SRC = "/tmp/claude-0/-home-user-Takuya-Okadas/2023b853-ee71-508e-8dbc-48a3fdf4ba86/scratchpad/oct.txt"

def norm_name(s):
    # strip filler/space chars
    t = s.replace('ᅠ',' ').replace('　',' ')
    if '谷本' in t: return '谷本'
    if '零奈' in t: return '横井'
    if '涼' in t and '風' in t: return '山口'
    if 'さいとう' in t or '斉藤' in t: return '斉藤'
    if '渡邉' in t or '渡辺' in t: return '渡邉'
    if 'まな' in t: return '伊東'
    return None

STAFF = ['谷本','伊東','山口','横井','斉藤','渡邉']
HOLIDAYS = {12}  # 2026-10 スポーツの日
WEEKEND = {3,4,10,11,17,18,24,25,31}  # 土日 in Oct 2026
def is_wknd_hol(d): return (d in WEEKEND) or (d in HOLIDAYS)

datehdr = re.compile(r'^2026\.10\.(\d\d)\s')
msgline = re.compile(r'^(\d\d):(\d\d)\s+(.*)$')

# time-report override patterns inside message, e.g. "11時", "19時半", "19:00", "10時半"
def extract_report_time(msg):
    m = re.search(r'(\d{1,2}):(\d{2})', msg)
    if m:
        return int(m.group(1))*60+int(m.group(2))
    m = re.search(r'(\d{1,2})時半', msg)
    if m:
        return int(m.group(1))*60+30
    m = re.search(r'(\d{1,2})時', msg)
    if m:
        return int(m.group(1))*60
    return None

days = {}  # day -> staff -> {'in':mins,'out':mins,'notes':[]}
cur = None
with open(SRC, encoding='utf-8') as f:
    for raw in f:
        line = raw.rstrip('\n')
        h = datehdr.match(line)
        if h:
            cur = int(h.group(1)); days[cur] = {}
            continue
        if cur is None: continue
        m = msgline.match(line)
        if not m:
            continue
        hh, mm, rest = int(m.group(1)), int(m.group(2)), m.group(3)
        if 'メッセージの送信を取り消し' in rest:
            continue
        name = norm_name(rest)
        if name is None:
            continue
        has_in = '出勤' in rest
        has_out = ('退社' in rest) or ('退勤' in rest)
        if not (has_in or has_out):
            continue
        stamp = hh*60+mm
        rep = extract_report_time(rest)
        # if a reported time exists and differs materially, it's a 申告 (forgot punch)
        t = stamp
        note = ''
        if rep is not None and abs(rep-stamp) >= 20:  # 申告 time differs from message time
            t = rep; note = f'申告({rep//60:02d}:{rep%60:02d})'
        rec = days[cur].setdefault(name, {'ins':[],'outs':[],'notes':[]})
        if has_in:
            rec['ins'].append(t)
            if note: rec['notes'].append('出'+note)
        if has_out:
            rec['outs'].append(t)
            if note: rec['notes'].append('退'+note)
# reduce to earliest in / latest out
MACHIDA_RULE = {'谷本','斉藤'}  # 出勤>=10:50 の日は町田勤務とみなし 11:00-20:00 固定
machida_days = {s:[] for s in MACHIDA_RULE}
for d in days:
    for s in days[d]:
        r = days[d][s]
        r['in'] = min(r['ins']) if r['ins'] else None
        r['out'] = max(r['outs']) if r['outs'] else None
        if s in MACHIDA_RULE and r['in'] is not None and r['in'] >= 650:  # 10:50
            r['in'] = 660; r['out'] = 1200  # 11:00-20:00
            r['notes'].append('町田11-20')
            machida_days[s].append(d)

def fmt(x):
    if x is None: return '--:--'
    if x>=1440: return f'+{(x-1440)//60:02d}:{(x-1440)%60:02d}'
    return f'{x//60:02d}:{x%60:02d}'

agg = {s:{'days':0,'work':0,'ot':0,'whd':0,'whd_days':0} for s in STAFF}
print("=== 2026年10月 日次 ===")
for d in sorted(days):
    tag = '[土日祝]' if is_wknd_hol(d) else ''
    for s in STAFF:
        if s in days[d]:
            r = days[d][s]
            iin, out = r['in'], r['out']
            if iin is not None and out is not None:
                o = out if out>iin else out+1440  # cross midnight
                work = (o-iin)-60
                ot = max(0, work-480)
                agg[s]['days']+=1; agg[s]['work']+=work; agg[s]['ot']+=ot
                if is_wknd_hol(d):
                    agg[s]['whd']+=1
                note = (' '+','.join(r['notes'])) if r['notes'] else ''
                print(f"10/{d:02d}{tag:7} {s}: {fmt(iin)}-{fmt(out)} 実{work//60}:{work%60:02d} 残{ot//60}:{ot%60:02d}{note}")
            else:
                print(f"10/{d:02d}{tag:7} {s}: IN={fmt(iin)} OUT={fmt(out)} ★不完全{' '+','.join(r['notes']) if r['notes'] else ''}")

print("\n=== 月次集計 ===")
print(f"{'氏名':<6}{'出勤':>4}{'実労働':>9}{'残業':>8}{'土日祝出勤':>8}")
for s in STAFF:
    a=agg[s]
    print(f"{s:<6}{a['days']:>4}{a['work']//60:>6}:{a['work']%60:02d}{a['ot']//60:>5}:{a['ot']%60:02d}{a['whd']:>8}")

# 土日祝の全出勤判定（山口・横井向け）
print("\n=== 土日祝(10日: 3,4,10,11,12,17,18,24,25,31) 出勤状況 ===")
whd_list = sorted(WEEKEND|HOLIDAYS)
for s in STAFF:
    worked=[d for d in whd_list if s in days[d] and days[d][s].get('in') is not None]
    missing=[d for d in whd_list if d not in worked]
    print(f"{s}: 出勤{len(worked)}/10  欠={missing}")
