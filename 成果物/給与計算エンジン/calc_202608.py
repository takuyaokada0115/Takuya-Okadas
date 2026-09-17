"""2026年8月分（9月支給）全社員 総支給を計算。

8月固有の反映:
- みなし残業枠25h・実残業は全員25h未満→追加残業ゼロ。
- 土日祝手当: 山口=8月土日祝を全出勤→5,000。横井=8/11欠→0。
- 皆勤手当: 各人の割当(谷本5,000/伊東5,000/山口6,900/横井6,900)。
- 通勤費: 8月実額。谷本=下北沢base9,566(8月は町田trip無し)/伊東0/山口23,620/
          横井=登戸-町田定期1/3(9,377)+登戸↔下北沢往復460×下北沢出勤日数。
"""
import dataclasses
from models import STAFF_MASTER, Attendance
from payroll import calculate, format_payslip
from perf_202608 import DATA, YEAR_MONTH

# 8月の上書き（土日祝手当・通勤費）。★通勤は8月実額（横井の下北沢日数は要確定）
AUG = {
    "S001": {"weekend_holiday_allowance": 0,     "commute_amount": 9_566},
    "S002": {"weekend_holiday_allowance": 0,     "commute_amount": 0},
    "S003": {"weekend_holiday_allowance": 5_000, "commute_amount": 23_620},
    # 横井: 土日祝0(8/11欠)。通勤=町田定期1/3(9,377)+下北沢日数×460 → 日数未確定のため町田分のみ暫定
    "S004": {"weekend_holiday_allowance": 0,     "commute_amount": 11_677},  # 町田定期1/3(9,377)+下北沢5日×460
}


def main():
    print(f"■ {YEAR_MONTH}分 総支給（9月支給）\n")
    rows = []
    for sid, (perf, att, is_tr) in DATA.items():
        staff = dataclasses.replace(STAFF_MASTER[sid], **AUG[sid])
        r = calculate(staff, perf, att, YEAR_MONTH, is_training=is_tr)
        print(format_payslip(r)); print()
        rows.append((sid, r))
    print("=== スタッフ別 総支給サマリ（8月分・9月支給）===")
    print(f"{'氏名':<8}{'月給':>9}{'みなし':>7}{'皆勤':>6}{'土日祝':>6}{'店長':>7}{'町田支援':>8}"
          f"{'インセ':>7}{'物販':>6}{'オプ':>6}{'指名料':>7}{'課税計':>9}{'通勤':>7}{'総支給':>9}")
    total = 0
    for sid, r in rows:
        teate_g = 20000 if r.manager_allowance else 0
        print(f"{r.name:<8}{r.monthly_salary:>9,}{r.deemed_ot_allowance:>7,}{r.diligence_allowance:>6,}"
              f"{r.weekend_holiday_allowance:>6,}{r.manager_allowance:>7,}{r.machida_support:>8,}"
              f"{r.sales_incentive:>7,}{r.retail_commission:>6,}{r.option_commission:>6,}{r.nomination_pay:>7,}"
              f"{r.taxable_gross:>9,}{r.commute:>7,}{r.total_gross:>9,}")
        total += r.total_gross
    print(f"\n社員4名 総支給合計: {total:,} 円（通勤8月実額確定: 横井=町田定期1/3+下北沢5日×460=11,677）")
    print("※松藤(業務委託)は別体系（8月の指名別売上内訳と勤務日数の売上明細CSVが必要）。")


if __name__ == "__main__":
    main()
