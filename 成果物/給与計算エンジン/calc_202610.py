"""2026年10月分（11月20日支給）総支給を算出。

データ源:
- HPBスタッフ別集計＋店販月別集計（両店・スタッフ別、店舗合計と完全一致検算済み）
- LINEタイムカード2026-10（残業・土日祝・労働日数）
- freee人事労務 前月明細（固定: 基本給/みなし残業代/皆勤手当、通勤費）

ルール:
- 売上インセンティブ = 合算総売上のルックアップ表（650k=6,500 … 100万=90,000、110万以上=10%）、65万未満=0
- 指名料 100%（店販内の指名料）
- 商品OP販売コミッション = (美容液[物販] + オプション) × 5%（四捨五入）  ※HBL beautyは要確認で別掲
- 店長手当20,000・町田業務支援手当10,000（谷本）
- 皆勤手当=従来どおり（freee固定値）/ みなし残業枠25h・実残業は全員25h未満→追加残業0
- 土日祝手当（山口・横井ほか対象者・当月の全土日祝出勤が条件）: 10月の土日祝=10日(3,4,10,11,12,17,18,24,25,31)
- 基本給・みなし・皆勤はfreee自動反映。freee入力対象＝変動手当（インセ/指名料/商品OPコミ/店長/町田支援/土日祝/通勤）
"""
import math

def incentive(total):
    tbl = [(650000,6500),(700000,14000),(750000,22500),(800000,32000),
           (850000,42500),(900000,54000),(950000,76000),(1000000,90000)]
    if total >= 1100000:
        return round(total*0.10)
    pay = 0
    for th,amt in tbl:
        if total >= th: pay = amt
    return pay  # <650k -> 0

def comm(biyoueki, option):          # 商品OP販売コミッション（四捨五入）
    return math.floor((biyoueki + option) * 0.05 + 0.5)

# combined(両店) per staff
S = {
 "谷本": dict(uriage=761550, nominatefee=34800, biyoueki=51410, hbl=3300, option=55000,
             base=217100, deemed=15400, kaikin=5000, tencho=20000, machida=10000, wkhol=0, commute=13166),  # 国領-下北沢定期9,566+下北沢町田往復720×5
 "伊東": dict(uriage=777350, nominatefee=13200, biyoueki=32450, hbl=0, option=53800,
             base=217100, deemed=12400, kaikin=6900, tencho=0, machida=0, wkhol=0, commute=0),
 "山口": dict(uriage=761400, nominatefee=6000,  biyoueki=12600, hbl=0, option=37700,
             base=213200, deemed=12400, kaikin=0, tencho=0, machida=0, wkhol=5000, commute=23620),
             # 皆勤手当=0: 自己都合早退(10/21・10/26が短時間勤務)により皆勤不成立
 "横井": dict(uriage=646590, nominatefee=2400,  biyoueki=9800,  hbl=0, option=25650,
             base=213200, deemed=12400, kaikin=6900, tencho=0, machida=0, wkhol=0, commute=15197),
}
# 新2名（要確認項目あり: 斉藤 土日祝/みなし枠, 渡邉 みなし/基本給日割/皆勤/通勤定期）
NEW = {
 "斉藤": dict(uriage=715790, nominatefee=1200, biyoueki=37400, hbl=0, option=32200,
             base=212500, deemed=12400, kaikin=6900, tencho=0, machida=0, wkhol=5000, commute=22726),
             # みなし残業代=12,400(有期契約どおり。freee現行7,440から訂正)
 "渡邉": dict(uriage=279500, nominatefee=0, biyoueki=4400, hbl=0, option=15000,
             base=212500, deemed=12400, kaikin=6900, tencho=0, machida=0, wkhol=0, commute=18130),
             # 通勤=祖師ヶ谷大蔵-下北沢 3ヶ月定期18,130を10月にまとめ支給。基本給は研修(10/1-16 @212,500)→本採用(10/17-31 @213,000)でfreee日割。みなし/皆勤は有期本採用分
}

def calc(d, hbl_in_bupan=True):   # HBL beautyも物販5%対象（ユーザー確定）
    inc = incentive(d["uriage"])
    bp = d["biyoueki"] + (d["hbl"] if hbl_in_bupan else 0)
    com = comm(bp, d["option"])
    # 変動手当（freee入力対象）
    var = dict(インセンティブ=inc, 指名料=d["nominatefee"], 商品OPコミ=com,
               店長手当=d["tencho"], 町田支援=d["machida"], 土日祝=d["wkhol"], 通勤=d["commute"])
    # 固定（freee自動）
    fix = dict(基本給=d["base"], みなし残業=d["deemed"], 皆勤=d["kaikin"])
    gross = sum(fix.values()) + sum(var.values())
    taxable = gross - d["commute"]
    return var, fix, gross, taxable

def show(name, d):
    var, fix, gross, taxable = calc(d)
    print(f"■ {name}")
    print(f"  [固定/freee自動] 基本給{fix['基本給']:,} みなし{fix['みなし残業']:,} 皆勤{fix['皆勤']:,}")
    print(f"  [変動/freee入力] インセ{var['インセンティブ']:,} 指名料{var['指名料']:,} "
          f"商品OPコミ{var['商品OPコミ']:,} 店長{var['店長手当']:,} 町田支援{var['町田支援']:,} "
          f"土日祝{var['土日祝']:,} 通勤{var['通勤']:,}")
    print(f"  → 課税支給計 {taxable:,} ＋通勤{var['通勤']:,} ＝ 総支給 {gross:,}\n")
    return gross

print("="*70)
print("2026年10月分（11/20支給）  ※社員4名=確定 / 新2名=要確認項目あり")
print("="*70)
tot = 0
for n in ["谷本","伊東","山口","横井"]:
    tot += show(n, S[n])
print(f"社員4名 総支給合計 = {tot:,} 円\n")
print("--- 新2名（暫定・下記★要確認） ---")
for n in ["斉藤","渡邉"]:
    show(n, NEW[n])
# 谷本HBL参考
v2,_,g2,_ = calc(S["谷本"], hbl_in_bupan=True)
print(f"参考) 谷本 物販にHBL beauty3,300を含める場合: 商品OPコミ {v2['商品OPコミ']:,} / 総支給 {g2:,}")
