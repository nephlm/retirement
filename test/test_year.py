import pytest

import retirement.year as year


class FakePlan(year.Plan):
    def __init__(self) -> None:
        self.income_source_ = [1, 0, 0]
        self.expenses_ = 50000
        self.portfolio_ = {"stocks": 0.75, "bonds": 0.2, "cash": 0.05}

    def portfolio(self, age):
        return self.portfolio_

    def income_source(self, age, starting):
        return self.income_source_

    def pre_tax_expenses(self, age):
        return self.expenses_


class TestYear:
    def test_basic(self):
        yr = year.Year(20, 1, 2, 3)
        assert yr.age == 20
        assert yr.starting.taxable.balance == 1
        assert yr.starting.ira.balance == 2
        assert yr.starting.roth.balance == 3

        for attr in ("processed", "growth", "inflation", "ending"):
            assert not getattr(yr, attr)

        assert isinstance(yr.plan, year.Plan)

    def test_annual_adjustment(self):
        yr = year.Year(52, 100, 100, 100)
        yr.stock_growth = 0.3
        yr.bond_growth = 0.2
        yr.inflation = 0.05
        growth = 0.3 * 0.75 + 0.2 * 0.2
        assert yr.growth == growth
        assert yr._annual_adjustment(1000) == 1000 * (1 + growth - 0.05)

    @pytest.mark.parametrize(
        "age, source, results",
        [
            (65, [0, 1, 0], (9000, 41000)),
            (65, [0.5, 0.5, 0], (25000, 25000)),
            (65, [0.1, 0.5, 0.4], (9000, 21000)),
        ],
    )
    def test_calculate_income(self, age, source, results):
        yr = year.Year(age, 600000, 700000, 800000)
        plan = FakePlan()
        plan.income_source_ = source
        yr.plan = plan
        assert yr._calculate_taxable_income(50000) == results

    @pytest.mark.parametrize(
        "input_income, results",
        [
            ((0, 50000), (9000, 41000)),
            ((25000, 25000), (25000, 25000)),
            ((50000, 0), (50000, 0)),
        ],
    )
    def test_adjust_for_forced_income(self, input_income, results):
        yr = year.Year(60, 600000, 700000, 800000)
        assert yr._adjust_for_forced_income(*input_income) == results

    @pytest.mark.parametrize(
        "input_income, taxes",
        [
            ((50000, 0), 4537.8435),
            ((25000, 25000), 5761.5935),
            ((0, 50000), 8705.34345),
            ((500, 5000), 999 * 0.052 + 999 * 0.062 + 999 * 0.072 + 101 * 0.0795),
        ],
    )
    def test_calculate_taxes(self, input_income, taxes):
        yr = year.Year(60, 600000, 700000, 800000)
        assert yr._calculate_taxes(*input_income) == pytest.approx(taxes)
