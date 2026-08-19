"""スタッフマスタ・月次実績・勤怠のデータモデルと登録済みマスタ。

出典: 労働条件通知書 兼 雇用契約書（各人）／新インセンティブ表／HPBサロンボード実績。
会社: Mana Lea株式会社 / 店舗: SSIN STUDIO（下北沢店・町田店）。
注記: 伊東 真菜 は 谷本 真澄 と同一条件（正社員・無期）。

■ HPB「店販」列の構造（2026-07 下北沢店実績で判明）:
  HPBのスタッフ別売上情報の「店販」列は〔指名料 + 回数券 + 物販商品(美容液等)〕の合算。
  したがって実績は以下に分解して保持する:
    - product_sales : 物販商品（美容液・HBL beauty 等）
    - coupon_sales  : 回数券
    - nomination_fee: 指名料
  「総売上」= 施術 + オプション +（店販=product+coupon+nomination）。
"""

from __future__ import annotations

from dataclasses import dataclass
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
    diligence_allowance: int      # 皆勤手当（freee明細では全員「皆勤手当」表記）
    weekend_holiday_allowance: int = 0  # 土日祝手当（有期のみ・★支給条件は暫定=月額固定）
    is_manager: bool = False      # 店長手当¥20,000の対象
    machida_support: int = 0      # 町田支援手当（谷本のみ・6月明細より¥10,000）
    store: str = ""               # 所属店舗
    hpb_name: str = ""            # HPBサロンボード上の表示名（実績突合キー）
    commute_amount: int = 0       # 実通勤交通費（非課税・上限3万で丸め）
    commute_cap: int = 30_000
    # 残業単価の分母（月平均所定労働時間）。★算定基礎・日数は要確認の暫定値。
    monthly_scheduled_hours: float = 173.8
    # 研修中月給（該当月のみ base_salary+fixed_ot_allowance の代わりに適用）
    training_salary: Optional[int] = None


@dataclass
class Performance:
    """月次実績（HPBスクレイピング結果）。金額は円・整数。

    HPBの「店販」列は product_sales + coupon_sales + nomination_fee に分解して保持する。
    """

    tech_sales: int = 0        # 施術売上
    option_sales: int = 0      # オプション売上
    product_sales: int = 0     # 物販商品（美容液・HBL等。指名料/回数券を除く）
    coupon_sales: int = 0      # 回数券
    nomination_fee: int = 0    # 指名料
    tech_count: int = 0        # 施術客数（参考）
    nomination_count: int = 0  # 指名数（参考）

    @property
    def retail_total(self) -> int:
        """HPBの「店販」列に相当（物販商品＋回数券＋指名料）。"""
        return self.product_sales + self.coupon_sales + self.nomination_fee

    @property
    def total_sales(self) -> int:
        """総売上（インセンティブ判定に使用・全て含む）。"""
        return self.tech_sales + self.option_sales + self.retail_total


@dataclass
class Attendance:
    """勤怠（OCR結果の集計）。時間は月合計。"""

    overtime_hours: float = 0.0     # 所定外労働（実残業）合計
    holiday_hours: float = 0.0      # 休日労働 合計
    late_night_hours: float = 0.0   # 深夜労働 合計


# --- 登録済みスタッフマスタ --------------------------------------------------

STAFF_MASTER: dict[str, Staff] = {
    # 谷本: 6月明細は月給217,100/みなし15,400だったが、ユーザー指示によりJuly分は
    # 基本給207,900/みなし残業代10,000へ補正（★みなし残業時間は10hのまま暫定）。
    # 通勤交通費は6月明細の実額を暫定使用（★7月実額は要確認）。
    "S001": Staff(
        staff_id="S001", name="谷本 真澄", employment_type="正社員",
        base_salary=207_900, fixed_ot_allowance=10_000, fixed_ot_hours=10,
        diligence_allowance=5_000, weekend_holiday_allowance=0,
        is_manager=True, machida_support=10_000, store="下北沢店", hpb_name="Masumi",
        # 7月通勤: 6月実額9,566 + 小田急 下北沢↔町田 往復1回(IC片道360×2=720) = 10,286
        commute_amount=10_286,
    ),
    "S002": Staff(
        staff_id="S002", name="伊東 真菜", employment_type="正社員",
        base_salary=217_100, fixed_ot_allowance=15_400, fixed_ot_hours=10,
        diligence_allowance=5_000, weekend_holiday_allowance=0,
        is_manager=False, store="下北沢店", hpb_name="Itou",
        commute_amount=0,
    ),
    "S003": Staff(
        staff_id="S003", name="山口 涼風", employment_type="有期契約",
        base_salary=213_200, fixed_ot_allowance=12_400, fixed_ot_hours=8,
        diligence_allowance=6_900, weekend_holiday_allowance=5_000,
        is_manager=False, store="町田店", hpb_name="Y.Suzuka",
        training_salary=212_500, commute_amount=23_620,  # 6月明細より（★7月要確認）
    ),
    "S004": Staff(
        staff_id="S004", name="横井 零奈", employment_type="有期契約",
        base_salary=213_200, fixed_ot_allowance=12_400, fixed_ot_hours=8,
        diligence_allowance=6_900, weekend_holiday_allowance=5_000,
        is_manager=False, store="下北沢店＋町田店", hpb_name="Y.Reina / Reina",
        # 7月通勤: 登戸↔下北沢往復460×6日(CSVで確定=2,760)
        #          + 町田=デフォルト(登戸-町田 通勤定期3ヶ月28,130の1/3=9,377) = 12,137
        training_salary=212_500, commute_amount=12_137,
    ),
}

# --- 未登録スタッフ（雇用条件が未提供） --------------------------------------
# HPB「Matsufuji」（下北沢店）は雇用契約書が未提供のためマスタ未登録。
# 実績は登録済み（perf_202607_shimokita.py）だが、基本給・雇用形態が不明で
# 総支給は算出不可。雇用条件の提供が必要。★
PENDING_STAFF = {
    "Matsufuji": {"store": "下北沢店", "reason": "雇用契約書 未提供（基本給・雇用形態・手当が不明）"},
}
