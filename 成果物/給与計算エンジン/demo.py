"""サンプル実績で全スタッフの総支給を計算し、明細を表示するデモ。

実行: python demo.py
実績値はサンプル。実運用では HPB実績（スクレイピング）と勤怠（OCR）で差し替える。
"""

from models import STAFF_MASTER, Attendance, Performance
from payroll import calculate, format_payslip

YEAR_MONTH = "2026-07"

# サンプル月次実績（staff_id → 実績・勤怠）
SAMPLE = {
    "S001": (Performance(700_000, 40_000, 20_000, 30_000), Attendance(overtime_hours=12)),
    "S002": (Performance(820_000, 30_000, 15_000, 25_000), Attendance(overtime_hours=10)),
    "S003": (Performance(680_000, 20_000, 10_000, 12_000), Attendance(overtime_hours=9)),
    "S004": (Performance(1_150_000, 60_000, 40_000, 50_000), Attendance(overtime_hours=15, holiday_hours=6)),
}


def main():
    total = 0
    for staff_id, (perf, att) in SAMPLE.items():
        staff = STAFF_MASTER[staff_id]
        r = calculate(staff, perf, att, YEAR_MONTH)
        print(format_payslip(r))
        print()
        total += r.total_gross
    print(f"【{YEAR_MONTH} 総支給 合計（{len(SAMPLE)}名）】 {total:,} 円")


if __name__ == "__main__":
    main()
