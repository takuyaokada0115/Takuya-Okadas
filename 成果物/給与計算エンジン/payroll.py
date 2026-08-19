"""総支給の計算エンジン（F1）。

責務: 各支給項目の内訳と総支給を算出するところまで。
控除（社保・源泉・住民税）は freee人事労務 に実装済みのため本システムでは計算しない。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import incentive
from models import Attendance, Performance, Staff

# 割増賃金率（雇用契約書・全員共通）
OT_RATE = 1.25          # 法定時間外（法定超）25%
OT_RATE_OVER60 = 1.50   # 月60時間超の部分 50%
HOLIDAY_RATE = 1.35     # 法定休日 35%
LATE_NIGHT_RATE = 0.25  # 深夜割増（加算分）25%

MANAGER_ALLOWANCE = 20_000  # 店長手当

# 物販コミッション5%の対象に「回数券」を含めるか。★要確認（暫定=含めない）。
# 指名料は物販5%の対象外（別途100%で支給）。
INCLUDE_COUPON_IN_RETAIL = False


@dataclass
class PayrollResult:
    """給与計算結果（総支給の内訳）。金額はすべて円・整数。"""

    staff_id: str
    name: str
    year_month: str

    # 支給項目
    monthly_salary: int = 0        # 月給（基本給。研修中は研修月給）
    deemed_ot_allowance: int = 0   # みなし残業代（固定残業手当）
    diligence_allowance: int = 0   # 皆勤手当
    weekend_holiday_allowance: int = 0  # 土日祝手当
    manager_allowance: int = 0     # 店長手当
    machida_support: int = 0       # 町田支援手当
    sales_incentive: int = 0       # 売上インセンティブ
    retail_commission: int = 0     # 物販コミッション
    option_commission: int = 0     # オプションコミッション
    nomination_pay: int = 0        # 指名料
    overtime_pay: int = 0          # 追加残業代（固定残業超過分）
    holiday_pay: int = 0           # 休日労働割増
    late_night_pay: int = 0        # 深夜割増
    commute: int = 0               # 通勤交通費（非課税）

    @property
    def taxable_gross(self) -> int:
        """課税対象の総支給（通勤交通費を除く）。"""
        return (
            self.monthly_salary
            + self.deemed_ot_allowance
            + self.diligence_allowance
            + self.weekend_holiday_allowance
            + self.manager_allowance
            + self.machida_support
            + self.sales_incentive
            + self.retail_commission
            + self.option_commission
            + self.nomination_pay
            + self.overtime_pay
            + self.holiday_pay
            + self.late_night_pay
        )

    @property
    def total_gross(self) -> int:
        """総支給額（通勤交通費を含む）。"""
        return self.taxable_gross + self.commute


def _hourly_wage(staff: Staff) -> float:
    """残業の1時間単価。★算定基礎は暫定で基本給のみ／分母は月平均所定労働時間。"""
    return staff.base_salary / staff.monthly_scheduled_hours


def calculate(
    staff: Staff,
    performance: Performance,
    attendance: Attendance,
    year_month: str,
    is_training: bool = False,
) -> PayrollResult:
    """1名・1か月分の総支給を計算する。"""
    r = PayrollResult(staff_id=staff.staff_id, name=staff.name, year_month=year_month)

    # 月給・みなし残業代（研修中は月給を研修月給で置換）
    if is_training and staff.training_salary is not None:
        r.monthly_salary = staff.training_salary
    else:
        r.monthly_salary = staff.base_salary
    r.deemed_ot_allowance = staff.fixed_ot_allowance

    # 契約手当
    r.diligence_allowance = staff.diligence_allowance
    r.weekend_holiday_allowance = staff.weekend_holiday_allowance
    r.manager_allowance = MANAGER_ALLOWANCE if staff.is_manager else 0
    r.machida_support = staff.machida_support

    # インセンティブ・コミッション
    r.sales_incentive = incentive.sales_incentive(performance.total_sales)
    retail_base = performance.product_sales
    if INCLUDE_COUPON_IN_RETAIL:
        retail_base += performance.coupon_sales
    r.retail_commission = incentive.retail_commission(retail_base)
    r.option_commission = incentive.option_commission(performance.option_sales)
    r.nomination_pay = incentive.nomination_pay(performance.nomination_fee)

    # 残業・割増（固定残業を超えた分のみ追加支給）
    hourly = _hourly_wage(staff)
    extra_ot = max(0.0, attendance.overtime_hours - staff.fixed_ot_hours)
    r.overtime_pay = round(extra_ot * hourly * OT_RATE)
    r.holiday_pay = round(attendance.holiday_hours * hourly * HOLIDAY_RATE)
    r.late_night_pay = round(attendance.late_night_hours * hourly * LATE_NIGHT_RATE)

    # 通勤交通費（非課税・上限で丸め）
    r.commute = min(staff.commute_amount, staff.commute_cap)

    return r


def format_payslip(r: PayrollResult) -> str:
    """内訳を人が読める給与明細テキストに整形する。"""
    def line(label, val):
        return f"  {label:<22}: {val:>10,}"
    lines = [f"=== {r.year_month} 給与明細（総支給）: {r.name}（{r.staff_id}）==="]
    items = [
        ("月給", r.monthly_salary),
        ("みなし残業代", r.deemed_ot_allowance),
        ("時間外労働手当(超過分)", r.overtime_pay),
        ("法定休日労働手当", r.holiday_pay),
        ("深夜労働手当", r.late_night_pay),
        ("皆勤手当", r.diligence_allowance),
        ("土日祝手当", r.weekend_holiday_allowance),
        ("店長手当", r.manager_allowance),
        ("町田支援手当", r.machida_support),
        ("商品販売コミッション", r.retail_commission),
        ("商品オプション販売コミッション", r.option_commission),
        ("売上インセンティブ", r.sales_incentive),
        ("指名料", r.nomination_pay),
    ]
    for label, val in items:
        if val:
            lines.append(line(label, val))
    lines.append("  " + "-" * 34)
    lines.append(line("課税支給計", r.taxable_gross))
    lines.append(line("通勤交通費(非課税)", r.commute))
    lines.append("  " + "=" * 34)
    lines.append(line("総支給額", r.total_gross))
    lines.append("  ※控除(社保・源泉・住民税)は freee人事労務 で計算")
    return "\n".join(lines)
