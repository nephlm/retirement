import pytest

import retirement.tax as tax


def test_lookup_rate():
    table = {0: 0, 800: 0.2, 4000: 0.25, 800000: 0.3}
    assert tax.lookup_rate(table, 5000) == 0.25


def test_get_all_brackets():
    table1 = {0: 0.1, 5000: 0.2, 50000: 0.3}
    table2 = {0: 0.1, 3000: 0.2, 30000: 0.3}
    table3 = {0: 0, 800: 0.2, 800000: 0.3, 4000: 0.25}
    keys = tax.get_all_brackets([table1, table2, table3])
    assert keys == [0, 800, 3000, 4000, 5000, 30000, 50000, 800000]


@pytest.fixture
def brackets():
    bracket1 = tax.Bracket(0, 0.1)
    bracket2 = tax.Bracket(500, 0.2, bracket1)
    bracket3 = tax.Bracket(5000, 0.3, bracket2)
    bracket1.next = bracket2
    bracket2.next = bracket3
    yield [bracket1, bracket2, bracket3]


class TestBrackets:
    def test_basic(self, brackets):
        assert len(brackets) == 3

        assert brackets[0].next == brackets[1]
        assert brackets[1].next == brackets[2]
        assert brackets[2].next is None

        assert brackets[0].previous is None
        assert brackets[1].previous == brackets[0]
        assert brackets[2].previous == brackets[1]

        assert brackets[0].marginal == 0.1
        assert brackets[1].marginal == 0.2
        assert brackets[2].marginal == 0.3

        assert brackets[0].start == 0
        assert brackets[1].start == 500
        assert brackets[2].start == 5000

    def test_end(self, brackets):
        assert brackets[0].end == 499
        assert brackets[1].end == 4999
        assert brackets[2].end is None

    def test_bracket_cost(self, brackets):
        assert pytest.approx(brackets[0].bracket_cost) == 499 * 0.1
        assert pytest.approx(brackets[1].bracket_cost) == (4999 - 500) * 0.2
        assert brackets[2].bracket_cost is None

    def test_bracket_cumulative(self, brackets):
        assert pytest.approx(brackets[0].cumulative) == 0
        assert pytest.approx(brackets[1].cumulative) == 49.9
        assert pytest.approx(brackets[2].cumulative) == 949.7

    @pytest.mark.parametrize(
        "amount,cost",
        [
            (0, 0),
            (250, 0),
            (499, 0),
            (500, 0.2),
            (1000, 501 * 0.2),
            (10000, 4499 * 0.2),
        ],
    )
    def test_partial_bracket_cost(self, brackets, amount, cost):
        assert pytest.approx(brackets[1].partial_bracket_cost(amount)) == cost


@pytest.fixture
def raw_table():
    return {0: 0.1, 500: 0.2, 5000: 0.3, 50000: 0.4}


class TestTaxTable:
    def test_basic(self, raw_table):
        tax_table = tax.TaxTable([raw_table], 0)

        assert tax_table.deduction == 0
        assert isinstance(tax_table.root_bracket, tax.Bracket)

        num_brackets = 1
        bracket = tax_table.root_bracket
        while bracket.next:
            num_brackets += 1
            bracket = bracket.next
        assert num_brackets == 4

    @staticmethod
    def check_bracket(bracket, start, marginal):
        assert bracket.start == start
        assert bracket.marginal == pytest.approx(marginal)
        return bracket.next

    def test_calculate_tax_brackets(self, raw_table):
        table2 = {0: 0.05, 9000: 0.15}
        tax_table = tax.TaxTable([raw_table, table2], 0)

        bracket1 = tax_table.root_bracket
        bracket2 = self.check_bracket(bracket1, 0, 0.15)
        bracket3 = self.check_bracket(bracket2, 500, 0.25)
        bracket4 = self.check_bracket(bracket3, 5000, 0.35)
        bracket5 = self.check_bracket(bracket4, 9000, 0.45)
        bracket6 = self.check_bracket(bracket5, 50000, 0.55)
        assert bracket6 is None

    @pytest.mark.parametrize(
        "amount, deduction, tax_amount",
        [
            (0, 500, 0),
            (510, 500, 1),
            (510, 0, 499 * 0.1 + 11 * 0.2),
            (30000, 0, 499 * 0.1 + 4499 * 0.2 + 25001 * 0.3),
        ],
    )
    def test_calculate_tax(self, amount, deduction, tax_amount, raw_table):
        tax_table = tax.TaxTable([raw_table], deduction=deduction)
        assert tax_table.calculate_tax(amount) == pytest.approx(tax_amount)


class TestCapitalGainsTax:
    @pytest.mark.parametrize(
        "amount, offset, deduction, tax_amount",
        [
            (0, 0, 500, 0),
            (510, 0, 500, 10 * 0.15),
            (510, 0, 0, 510 * 0.15),
            (30000, 0, 0, 30000 * 0.15),
            (1000, 500, 500, 1000 * 0.15),
            (1000, 100, 300, 800 * 0.15),
        ],
    )
    def test_calculate_tax(self, amount, offset, deduction, tax_amount, raw_table):
        tax_table = tax.CapitalTaxTable([{}], deduction=deduction)
        assert tax_table.calculate_tax(amount, offset) == pytest.approx(tax_amount)


class TestState:
    @pytest.mark.parametrize(
        "income, tax_amount",
        [
            (0, 0),
            (2400, 0),
            (3000, 600 * 0.052),
            (3399, 999 * 0.052),
            (3400, 999 * 0.052 + 1 * 0.062),
            (5000, 999 * 0.052 + 999 * 0.062 + 601 * 0.072),
        ],
    )
    def test_state_rates(self, income, tax_amount):
        table = tax.STATE_TAX_TABLE
        assert table.calculate_tax(income) == pytest.approx(tax_amount)
