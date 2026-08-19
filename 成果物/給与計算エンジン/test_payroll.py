"""総支給計算エンジンのテスト。

実行: python -m pytest test_payroll.py -q
（pytest未導入でも `python test_payroll.py` で簡易実行可能）
"""

import incentive
from models import STAFF_MASTER, Attendance, Performance
from payroll import calculate


# --- 売上インセンティブ表（ルックアップ）の境界テスト --------------------------

def test_incentive_below_floor():
    assert incentive.sales_incentive(649_999) == 0
    assert incentive.sales_incentive(0) == 0


def test_incentive_exact_thresholds():
    assert incentive.sales_incentive(650_000) == 6_500
    assert incentive.sales_incentive(700_000) == 14_000
    assert incentive.sales_incentive(750_000) == 22_500
    assert incentive.sales_incentive(800_000) == 32_000
    assert incentive.sales_incentive(850_000) == 42_500
    assert incentive.sales_incentive(900_000) == 54_000
    assert incentive.sales_incentive(950_000) == 76_000     # ％が飛ぶ行(8%)
    assert incentive.sales_incentive(1_000_000) == 90_000


def test_incentive_between_thresholds():
    assert incentive.sales_incentive(730_000) == 14_000     # [700k,750k)
    assert incentive.sales_incentive(949_999) == 54_000     # [900k,950k)
    assert incentive.sales_incentive(1_050_000) == 90_000   # [1,000k,1,100k)


def test_incentive_rate_zone():
    assert incentive.sales_incentive(1_100_000) == 110_000  # ×10%
    assert incentive.sales_incentive(1_200_000) == 120_000
    assert incentive.sales_incentive(1_500_000) == 150_000


# --- コミッション --------------------------------------------------------------

def test_commissions():
    assert incentive.retail_commission(40_000) == 2_000
    assert incentive.option_commission(20_000) == 1_000
    assert incentive.nomination_pay(30_000) == 30_000


# --- 総支給（店長・谷本、追加残業なしのクリーンケース）------------------------

def test_manager_gross_no_extra_ot():
    staff = STAFF_MASTER["S001"]  # 谷本 真澄（正社員・店長）
    perf = Performance(tech_sales=700_000, product_sales=40_000,
                       option_sales=20_000, nomination_fee=30_000)
    # 総売上 = 790,000 → インセンティブ 22,500
    # 実残業10h = 固定残業10h → 追加残業0
    att = Attendance(overtime_hours=10)
    r = calculate(staff, perf, att, "2026-07")

    assert r.monthly_salary == 207_900      # 補正後の基本給
    assert r.deemed_ot_allowance == 10_000  # 補正後のみなし残業代
    assert r.diligence_allowance == 5_000
    assert r.manager_allowance == 20_000
    assert r.machida_support == 10_000
    assert r.sales_incentive == 22_500
    assert r.retail_commission == 2_000
    assert r.option_commission == 1_000
    assert r.nomination_pay == 30_000
    assert r.overtime_pay == 0
    assert r.taxable_gross == 308_400


# --- 追加残業代（固定残業超過分のみ）------------------------------------------

def test_extra_overtime():
    staff = STAFF_MASTER["S001"]
    perf = Performance()
    att = Attendance(overtime_hours=12)     # 固定10h → 超過2h
    r = calculate(staff, perf, att, "2026-07")

    expected = round(2 * (207_900 / 173.8) * 1.25)
    assert r.overtime_pay == expected
    assert r.overtime_pay == 2_991


# --- 有期契約・土日祝手当・研修中月給 -----------------------------------------

def test_fixed_term_with_allowances():
    staff = STAFF_MASTER["S003"]  # 山口 涼風（有期契約）
    perf = Performance(tech_sales=650_000)  # 総売上650,000 → 6,500
    att = Attendance(overtime_hours=8)      # 固定8h → 追加0
    r = calculate(staff, perf, att, "2026-05")

    assert r.monthly_salary == 213_200
    assert r.deemed_ot_allowance == 12_400
    assert r.diligence_allowance == 6_900   # 皆勤手当
    assert r.weekend_holiday_allowance == 5_000
    assert r.manager_allowance == 0
    assert r.sales_incentive == 6_500
    assert r.taxable_gross == 244_000


def test_retail_decomposition_and_nomination():
    # HPB「店販」= 物販商品 + 回数券 + 指名料 の分解を検証（Masumi/谷本の実データ）
    perf = Performance(tech_sales=609_580, option_sales=51_600,
                       product_sales=27_000, coupon_sales=34_200, nomination_fee=31_200)
    assert perf.retail_total == 92_400          # HPB店販列と一致
    assert perf.total_sales == 753_580          # HPB総売上列と一致

    staff = STAFF_MASTER["S001"]
    r = calculate(staff, perf, Attendance(), "2026-07")
    assert r.sales_incentive == 22_500          # 753,580 → [750k,800k)
    assert r.nomination_pay == 31_200           # 指名料100%
    assert r.retail_commission == 1_350         # 物販商品27,000×5%（回数券・指名料は対象外）
    assert r.option_commission == 2_580         # 51,600×5%


def test_training_month():
    staff = STAFF_MASTER["S003"]
    perf = Performance()
    att = Attendance()
    r = calculate(staff, perf, att, "2026-01", is_training=True)
    assert r.monthly_salary == 212_500      # 研修中月給で置換


if __name__ == "__main__":
    # pytestなしでも走る簡易ランナー
    import sys
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    sys.exit(1 if failed else 0)
