"""基本面純計算；期間／科目由呼叫端明確提供，缺值不算成零。"""

import calendar
import math
from datetime import date


def previous_quarter(period: str) -> str:
    day = date.fromisoformat(period)
    if day.month not in (3, 6, 9, 12) or day.day != calendar.monthrange(day.year, day.month)[1]:
        raise ValueError("財報日期必須為曆年季末")
    year, month = (day.year - 1, 12) if day.month == 3 else (day.year, day.month - 3)
    return date(year, month, calendar.monthrange(year, month)[1]).isoformat()


def previous_month(period: str) -> str:
    day = date.fromisoformat(period)
    return date(day.year - (day.month == 1), 12 if day.month == 1 else day.month - 1, 1).isoformat()


def number(value) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("缺少有效數值")
    return float(value)


def positive(value) -> float:
    value = number(value)
    if value <= 0:
        raise ValueError("分母必須大於零")
    return value


def roe_ttm(net_incomes: list, opening_equity, closing_equity) -> float:
    if len(net_incomes) != 4:
        raise ValueError("ROE 需四個連續單季淨利")
    average = positive(opening_equity) / 2 + positive(closing_equity) / 2
    return number(sum(number(value) for value in net_incomes) / average * 100)


def revenue_yoy(current, prior_year) -> float:
    current = number(current)
    if current < 0:
        raise ValueError("營收不可為負數")
    return number((current / positive(prior_year) - 1) * 100)


def piotroski_score(current: dict, previous: dict) -> dict:
    """IFRS 研究映射：年度淨利／CFO、期初資產；槓桿用平均資產。

    equity_issued 需明確布林事實，不能用股本變化或空白科目猜測。
    九項各一分；任何一項缺資料，總分為 None，保留已能計算的訊號。
    """
    def roa(data):
        return number(number(data.get("net_income")) / positive(data.get("opening_assets")))

    def leverage(data):
        debt = number(data.get("long_term_debt"))
        if debt < 0:
            raise ValueError("長期負債不可負數")
        return number(debt / (positive(data.get("opening_assets")) / 2 + positive(data.get("assets")) / 2))

    def liquidity(data):
        assets = number(data.get("current_assets"))
        if assets < 0:
            raise ValueError("流動資產不可負數")
        return number(assets / positive(data.get("current_liabilities")))

    def margin(data):
        return number(number(data.get("gross_profit")) / positive(data.get("revenue")))

    def turnover(data):
        return number(positive(data.get("revenue")) / positive(data.get("opening_assets")))

    def no_equity_issued():
        issued = current.get("equity_issued")
        if type(issued) is not bool:
            raise ValueError("缺少當年是否發行普通股的可靠紀錄")
        return not issued

    criteria = [
        ("positive_roa", lambda: roa(current) > 0),
        ("positive_cfo", lambda: number(number(current.get("operating_cash_flow")) / positive(current.get("opening_assets"))) > 0),
        ("improving_roa", lambda: roa(current) > roa(previous)),
        ("cash_exceeds_profit", lambda: number(current.get("operating_cash_flow")) > number(current.get("net_income"))),
        ("lower_leverage", lambda: leverage(current) < leverage(previous)),
        ("improving_liquidity", lambda: liquidity(current) > liquidity(previous)),
        ("no_equity_issued", no_equity_issued),
        ("improving_margin", lambda: margin(current) > margin(previous)),
        ("improving_turnover", lambda: turnover(current) > turnover(previous)),
    ]
    signals = []
    for name, calculate in criteria:
        try:
            signals.append({"id": name, "passed": bool(calculate()), "reason": None})
        except (ValueError, ArithmeticError) as error:
            signals.append({"id": name, "passed": None, "reason": str(error)})
    complete = all(signal["passed"] is not None for signal in signals)
    return {"version": "piotroski-ifrs-v1", "score": sum(s["passed"] for s in signals) if complete else None,
            "score_max": 9, "known_signals": sum(s["passed"] is not None for s in signals), "signals": signals}
