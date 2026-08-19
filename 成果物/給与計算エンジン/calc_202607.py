"""2026年7月分（8月支給）全スタッフ総支給を計算し、スタッフ別に出力する。"""

import incentive
from models import STAFF_MASTER, Attendance
from payroll import calculate, format_payslip
from perf_202607 import DATA, YEAR_MONTH, MATSUFUJI


def main():
    print(f"■ 下北沢店＋町田店 {YEAR_MONTH}分 総支給（8月支給）\n")
    rows = []
    for staff_id, (perf, att, is_tr) in DATA.items():
        staff = STAFF_MASTER[staff_id]
        r = calculate(staff, perf, att, YEAR_MONTH, is_training=is_tr)
        print(format_payslip(r))
        print(f"  （残業：月{att.overtime_hours:.2f}h − 固定{staff.fixed_ot_hours:.0f}h "
              f"→ 追加{max(0, att.overtime_hours - staff.fixed_ot_hours):.2f}h）\n")
        rows.append(r)

    # 松藤（業務委託・別体系）
    print("--- 松藤 華奈（業務委託フルコミッション・下北沢）---")
    print("    gyomu_itaku.py で計算（施術指名なし50%/指名60%は経費10%控除後、店販/オプ10%、交通費=片道160×2×勤務日数）。")
    print("    7月分は『施術売上(指名なし)/指名売上』の内訳と勤務日数が必要（HPB要約+勤怠では不足）。\n")

    # サマリ表
    print("=== スタッフ別 総支給サマリ（7月分・8月支給）===")
    print(f"{'氏名':<8}{'月給':>9}{'みなし':>7}{'諸手当':>8}{'インセ':>7}{'物販':>6}{'オプ':>6}"
          f"{'指名料':>7}{'時間外':>7}{'休日':>6}{'通勤':>7}{'総支給':>9}")
    total = 0
    for r in rows:
        teate = r.diligence_allowance + r.weekend_holiday_allowance + r.manager_allowance + r.machida_support
        print(f"{r.name:<8}{r.monthly_salary:>9,}{r.deemed_ot_allowance:>7,}{teate:>8,}{r.sales_incentive:>7,}"
              f"{r.retail_commission:>6,}{r.option_commission:>6,}{r.nomination_pay:>7,}"
              f"{r.overtime_pay:>7,}{r.holiday_pay:>6,}{r.commute:>7,}{r.total_gross:>9,}")
        total += r.total_gross
    print(f"{'合計':<8}{total:>76,}")
    print("\n※諸手当=皆勤+土日祝+店長+町田支援。控除(社保・源泉・住民税)は freee人事労務 で計算。")
    print("※みなし残業の枠=月25時間。実残業(実働-8h)は全員25h未満のため追加残業ゼロ。みなし残業代は契約額を据置(谷本10,000/伊東15,400/山口横井12,400)。")
    print("※谷本: 基本給207,900、7/21半日休日出勤(4h暫定)を法定休日労働手当に反映。")
    print("※通勤交通費は7月実績(谷本=下北沢+町田往復1回、横井=下北沢6日実費+町田定期1/3)。")
    print("※松藤(業務委託)は gyomu_itaku.py で別体系計算。7月の売上内訳(施術指名なし/指名売上)と勤務日数が必要。")


if __name__ == "__main__":
    main()
