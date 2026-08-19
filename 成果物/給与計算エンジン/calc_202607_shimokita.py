"""下北沢店 2026年7月分（8月支給）の総支給を計算する。

勤怠（残業）は勤怠OCR未取得のため 0 として計算（残業代は後日反映）。
物販5%は暫定で「回数券を含めない」。回数券を含める場合の差分も併記する。
"""

import incentive
import payroll
from models import STAFF_MASTER, Attendance
from payroll import calculate, format_payslip
from perf_202607_shimokita import PERF, STORE, YEAR_MONTH


def main():
    print(f"■ {STORE} {YEAR_MONTH}分 総支給（8月支給・勤怠/残業は未反映）\n")
    total = 0
    for hpb_name, (staff_id, perf) in PERF.items():
        if staff_id is None:
            print(f"--- {hpb_name}: マスタ未登録のため総支給は算出不可（雇用条件の提供待ち） ---")
            # 売上由来の項目だけ参考表示
            inc = incentive.sales_incentive(perf.total_sales)
            nom = incentive.nomination_pay(perf.nomination_fee)
            ret = incentive.retail_commission(perf.product_sales)
            opt = incentive.option_commission(perf.option_sales)
            print(f"    総売上 {perf.total_sales:,} → インセ {inc:,} / 指名料 {nom:,} / 物販 {ret:,} / オプ {opt:,}")
            print(f"    売上由来コミッション計 {inc + nom + ret + opt:,}（基本給・手当は未確定）\n")
            continue

        staff = STAFF_MASTER[staff_id]
        r = calculate(staff, perf, Attendance(), YEAR_MONTH)
        print(format_payslip(r))
        # 回数券を物販5%対象に含めた場合の差分
        if perf.coupon_sales:
            diff = incentive.retail_commission(perf.coupon_sales)
            print(f"  （参考）回数券{perf.coupon_sales:,}を物販5%に含めると +{diff:,}")
        print()
        total += r.total_gross

    print(f"【{STORE} {YEAR_MONTH} 総支給合計（マスタ登録済みのみ）】 {total:,} 円")
    print(f"  ※Matsufuji は雇用条件未登録のため未算入。物販5%の回数券扱いは暫定（含めない）。")


if __name__ == "__main__":
    main()
