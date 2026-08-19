"""業務委託フルコミッション計算（松藤華奈さん方式）。

出典: Google Drive「松藤華奈様_コミッション計算_FY26」/ matsufuji_1.xlsx / 下北沢売上明細CSV。
※料率は期間で改定されている（〜6月=旧、7月〜=新）。RateSet で切替。
ロジック:
  ・ご自身の顧客売上 × 90%(経費10%控除後) × own率
  ・施術売上(指名なし)  × 90%(経費10%控除後) × treat率
  ・指名売上           × 90%(経費10%控除後) × nom率
  ・店販売上 × retail率（経費控除なし）
  ・オプション売上 × option率（経費控除なし）
  ・交通費 = 片道運賃 × 2 × 勤務日数（transport=Trueのとき・実費）
  ・支給合計 = 5種コミッション + 交通費
"""

import math
from dataclasses import dataclass

EXPENSE_RATE = 0.10  # 経費控除率（施術・指名・自身顧客のみ）
# 規定エクセル(松藤華奈様_コミッション計算_FY26)は ROUNDDOWN(切り捨て)


@dataclass
class RateSet:
    own: float
    treat: float
    nom: float
    retail: float
    option: float
    transport: bool  # 交通費を支給するか


# 〜2026年6月（旧料率）
RATES_OLD = RateSet(own=0.70, treat=0.50, nom=0.60, retail=0.10, option=0.10, transport=True)
# 2026年7月〜（新料率：施術/指名/自身顧客を引下げ、店販/オプ5%、交通費なし）
RATES_NEW = RateSet(own=0.60, treat=0.40, nom=0.50, retail=0.05, option=0.05, transport=False)


@dataclass
class GyomuInput:
    own_customer_sales: int = 0      # ご自身の顧客売上（例: フジイユメカ）
    treatment_sales: int = 0         # 施術売上（指名なし）
    nomination_sales: int = 0        # 指名売上（施術・指名あり）
    retail_sales: int = 0            # 店販売上（指名料は除外）
    option_sales: int = 0            # オプション売上
    work_days: int = 0               # 勤務日数
    one_way_fare: int = 160          # 片道運賃


def calc(g: GyomuInput, rates: RateSet = RATES_OLD) -> dict:
    net = 1 - EXPENSE_RATE
    own = math.floor(g.own_customer_sales * net * rates.own)
    treat = math.floor(g.treatment_sales * net * rates.treat)
    nom = math.floor(g.nomination_sales * net * rates.nom)
    retail = math.floor(g.retail_sales * rates.retail)
    option = math.floor(g.option_sales * rates.option)
    transport = g.one_way_fare * 2 * g.work_days if rates.transport else 0
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
    # 6月検算（旧料率）: 施術406,700 / 指名38,300 / 店販7,200 / オプ22,600 / 勤務17日
    june = GyomuInput(treatment_sales=406_700, nomination_sales=38_300,
                      retail_sales=7_200, option_sales=22_600, work_days=17)
    assert calc(june, RATES_OLD)["支給合計"] == 212_117
    print("6月検算OK (212,117)")

    # 2026年7月（新料率・8月支給）: 下北沢売上明細CSVより
    #  施術(指名なし)352,480 / 施術(指名あり)24,800 / 店販(物販)15,400 / オプ19,100
    #  ご自身の顧客(フジイユメカ)=0(当月は施術なし) / 指名料は売上から除外 / 交通費なし
    jul = GyomuInput(own_customer_sales=0, treatment_sales=352_480,
                     nomination_sales=24_800, retail_sales=15_400, option_sales=19_100)
    rj = calc(jul, RATES_NEW)
    print("\n2026年7月 松藤 業務委託（新料率）:")
    for k, v in rj.items():
        print(f"  {k}: {v:,}")
    assert rj["支給合計"] == 139_777, rj["支給合計"]
    print("7月 支給合計 = 139,777（規定エクセルROUNDDOWN準拠）")
