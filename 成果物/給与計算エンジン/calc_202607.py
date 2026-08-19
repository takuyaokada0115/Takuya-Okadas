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

    # Matsufuji（未登録）参考
    inc = incentive.sales_incentive(MATSUFUJI.total_sales)
    print("--- 松藤（Matsufuji/下北沢）: マスタ未登録のため総支給算出不可 ---")
    print(f"    総売上 {MATSUFUJI.total_sales:,} → インセ {inc:,} / "
          f"指名料 {MATSUFUJI.nomination_fee:,} / 物販 {incentive.retail_commission(MATSUFUJI.product_sales):,} / "
          f"オプ {incentive.option_commission(MATSUFUJI.option_sales):,}\n")

    # サマリ表
    print("=== スタッフ別 総支給サマリ（7月分・8月支給）===")
    print(f"{'氏名':<8}{'基本+固定残業':>12}{'手当計':>8}{'インセ':>8}{'物販':>7}{'オプ':>7}{'指名料':>8}{'残業':>8}{'総支給':>10}")
    total = 0
    for r in rows:
        teate = r.diligence_allowance + r.weekend_holiday_allowance + r.manager_allowance
        print(f"{r.name:<8}{r.base_component:>12,}{teate:>8,}{r.sales_incentive:>8,}"
              f"{r.retail_commission:>7,}{r.option_commission:>7,}{r.nomination_pay:>8,}"
              f"{r.overtime_pay:>8,}{r.total_gross:>10,}")
        total += r.total_gross
    print(f"{'合計':<8}{'':>12}{'':>8}{'':>8}{'':>7}{'':>7}{'':>8}{'':>8}{total:>10,}")
    print("\n※控除(社保・源泉・住民税)は freee人事労務 で計算。")
    print("※谷本さんは7/21休日出勤(半日・採用面接)の休日出勤手当が別途必要（ルール未確認・未反映）。")
    print("※松藤さんはマスタ未登録のため未算入。")


if __name__ == "__main__":
    main()
