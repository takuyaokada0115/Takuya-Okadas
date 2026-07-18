"""スタッフマスタ・月次実績・勤怠のデータモデルと登録済みマスタ。

出典: 労働条件通知書 兼 雇用契約書（各人）／新インセンティブ表。
会社: Mana Lea株式会社 / 店舗: SSIN STUDIO。
注記: 伊東 真菜 は 谷本 真澄 と同一条件（正社員・無期）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Staff:
    """スタッフマスタ（事前登録）。"""

    staff_id: str
    name: str
    employment_type: str          # "正社員" | "有期契約"
    base_salary: int              # 基本給
    fixed_ot_allowance: int       # 固定残業手当
    fixed_ot_hours: float         # 固定残業時間
    diligence_allowance: int      # 精勤手当（正社員）/ 皆勤手当（有期）
    weekend_holiday_allowance: int = 0  # 土日祝手当（有期のみ・★支給条件は暫定=月額固定）
    is_manager: bool = False      # 店長手当¥20,000の対象
    commute_amount: int = 0       # 実通勤交通費（非課税・上限3万で丸め）
    commute_cap: int = 30_000
    # 残業単価の分母（月平均所定労働時間）。★算定基礎・日数は要確認の暫定値。
    monthly_scheduled_hours: float = 173.8
    # 研修中月給（該当月のみ base_salary+fixed_ot_allowance の代わりに適用）
    training_salary: Optional[int] = None


@dataclass
class Performance:
    """月次実績（HPBスクレイピング結果）。"""

    tech_sales: int = 0        # 技術売上
    retail_sales: int = 0      # 物販（店販）売上
    option_sales: int = 0      # オプション売上
    nomination_fee: int = 0    # 指名料売上

    @property
    def total_sales(self) -> int:
        """インセンティブ判定に使う総売上（全て含む・確定事項）。"""
        return self.tech_sales + self.retail_sales + self.option_sales + self.nomination_fee


@dataclass
class Attendance:
    """勤怠（OCR結果の集計）。時間は月合計。"""

    overtime_hours: float = 0.0     # 所定外労働（実残業）合計
    holiday_hours: float = 0.0      # 休日労働 合計
    late_night_hours: float = 0.0   # 深夜労働 合計


# --- 登録済みスタッフマスタ（4名） ------------------------------------------

STAFF_MASTER: dict[str, Staff] = {
    "S001": Staff(
        staff_id="S001", name="谷本 真澄", employment_type="正社員",
        base_salary=217_100, fixed_ot_allowance=15_400, fixed_ot_hours=10,
        diligence_allowance=5_000, weekend_holiday_allowance=0,
        is_manager=True,
    ),
    "S002": Staff(
        staff_id="S002", name="伊東 真菜", employment_type="正社員",
        base_salary=217_100, fixed_ot_allowance=15_400, fixed_ot_hours=10,
        diligence_allowance=5_000, weekend_holiday_allowance=0,
        is_manager=False,
    ),
    "S003": Staff(
        staff_id="S003", name="山口 涼風", employment_type="有期契約",
        base_salary=213_200, fixed_ot_allowance=12_400, fixed_ot_hours=8,
        diligence_allowance=6_900, weekend_holiday_allowance=5_000,
        is_manager=False, training_salary=212_500,  # 研修: 2026/1
    ),
    "S004": Staff(
        staff_id="S004", name="横井 零奈", employment_type="有期契約",
        base_salary=213_200, fixed_ot_allowance=12_400, fixed_ot_hours=8,
        diligence_allowance=6_900, weekend_holiday_allowance=5_000,
        is_manager=False, training_salary=212_500,  # 研修: 2025/10
    ),
}
