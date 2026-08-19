"""業務委託フルコミッション計算（松藤華奈さん方式）。

出典: Google Drive「松藤華奈様_コミッション計算_FY26」/ matsufuji_1.xlsx。
ロジック:
  ・ご自身の顧客売上 × 90%(経費10%控除後) × 70% = ご自身の顧客コミッション
  ・施術売上(指名なし)  × 90%(経費10%控除後) × 50% = 施術コミッション
  ・指名売上           × 90%(経費10%控除後) × 60% = 指名コミッション
  ・店販売上 × 10%（経費控除なし）
  ・オプション売上 × 10%（経費控除なし）
  ・交通費 = 片道運賃 × 2 × 勤務日数（実費・経費控除なし）
  ・支給合計 = 5種コミッション + 交通費
※雇用（正社員/有期）とは別体系。店販/オプションは10%（社員は5%）。
"""

from dataclasses import dataclass

EXPENSE_RATE = 0.10          # 経費控除率（施術・指名・自身顧客）
RATE_OWN = 0.70             # ご自身の顧客
RATE_TREATMENT = 0.50       # 施術（指名なし）
RATE_NOMINATION = 0.60      # 指名売上
RATE_RETAIL_OPTION = 0.10   # 店販/オプション


@dataclass
class GyomuInput:
    own_customer_sales: int = 0      # ご自身の顧客売上
    treatment_sales: int = 0         # 施術売上（指名なし）
    nomination_sales: int = 0        # 指名売上
    retail_sales: int = 0            # 店販売上
    option_sales: int = 0            # オプション売上
    work_days: int = 0               # 勤務日数
    one_way_fare: int = 160          # 片道運賃


def calc(g: GyomuInput) -> dict:
    net = 1 - EXPENSE_RATE
    own = round(g.own_customer_sales * net * RATE_OWN)
    treat = round(g.treatment_sales * net * RATE_TREATMENT)
    nom = round(g.nomination_sales * net * RATE_NOMINATION)
    retail = round(g.retail_sales * RATE_RETAIL_OPTION)
    option = round(g.option_sales * RATE_RETAIL_OPTION)
    transport = g.one_way_fare * 2 * g.work_days
    total = own + treat + nom + retail + option + transport
    return {
        "ご自身の顧客コミッション": own,
        "施術コミッション(指名なし)": treat,
        "指名コミッション": nom,
        "店販コミッション": retail,
        "オプションコミッション": option,
        "交通費": transport,
        "支給合計": total,
    }


if __name__ == "__main__":
    # 検算: 6月実績（xlsxより）施術406,700 / 指名38,300 / 店販7,200 / オプ22,600 / 勤務17日
    june = GyomuInput(treatment_sales=406_700, nomination_sales=38_300,
                      retail_sales=7_200, option_sales=22_600, work_days=17)
    r = calc(june)
    for k, v in r.items():
        print(f"{k}: {v:,}")
    assert r["支給合計"] == 212_117, r["支給合計"]
    print("6月検算OK (212,117)")
