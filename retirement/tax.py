from dataclasses import dataclass

FED_STANDARD_DEDUCTION = 12950
STATE_STANDARD_DEDUCTION = 2400
CAPITAL_STANDARD_DEDUCTION = 44625

REGULAR_TAX = "regular"
CAPITAL_TAX = "capital"

FED_TAX_RAW = {
    0: 0.10,
    11676: 0.15,
    47476: 0.25,
    114750: 0.28,
    239301: 0.33,
    520301: 0.35,
    522426: 0.396,
}

STATE_TAX_RAW = {
    0: 0.02,
    1000: 0.03,
    2000: 0.04,
    3000: 0.0475,
    100000: 0.05,
    125000: 0.0525,
    150000: 0.055,
    250000: 0.0575,
}

LOCAL_TAX_RAW = {0: 0.032}
CAPITAL_TAX_RAW = {0: 0.15}


def lookup_rate(table: list[dict[int, float]], amount: float):
    """
    _summary_

    Args:
        table: A dict with key is start value of the bracket and the value is the
                marginal rate.
        amount: The value we are looking up the marginal rate for.

    Returns:
        The marginal rate
    """
    keys = sorted(table.keys())
    rate = None
    for key in keys:
        if key <= amount or rate is None:
            rate = table[key]
        else:
            break
    return rate


def get_all_brackets(tables: list[dict[int, float]]) -> list[int]:
    """
    Args:
        tables (_type_):List of dicts with the keys are the starting value of the bracket.

    Returns:
        The list of all starting values from all tables.
    """
    keys = set()
    for table in tables:
        for key in table:
            keys.add(key)
    return sorted(list(keys))


@dataclass
class Bracket:
    start: int
    marginal: float
    previous: "Bracket" = None
    next: "Bracket" = None

    @property
    def end(self):
        if not self.next:
            return None
        return self.next.start - 1

    @property
    def bracket_cost(self):
        """The cost of this complete bracket not counting previous brackets"""
        if self.next:
            return ((self.next.start - 1) - self.start) * self.marginal
        else:
            return None

    @property
    def cumulative(self):
        """The cost of all previous brackets"""
        if self.previous:
            return self.previous.cumulative + self.previous.bracket_cost
        else:
            return 0

    def partial_bracket_cost(self, amount):
        if amount < self.start:
            return 0
        if self.end and amount >= self.end:
            return self.bracket_cost
        if self.previous:
            return (amount - self.previous.end) * self.marginal
        return amount * self.marginal

    def __repr__(self):
        return (
            f"<Bracket: start: {self.start}, end: {self.end}, "
            + f"cumultive: {self.cumulative}, marginal: {self.marginal}>"
        )


class TaxTable:
    def __init__(self, tables, deduction) -> None:
        self.root_bracket = None
        self.tables = tables
        self.deduction = deduction
        self.calculate_tax_brackets()

    def calculate_tax_brackets(self):
        bracket_keys = get_all_brackets(self.tables)
        # print(bracket_keys)

        last_bracket = None
        for key in bracket_keys:
            marginal = sum([lookup_rate(x, key) for x in self.tables])

            bracket = Bracket(start=key, marginal=marginal, previous=last_bracket)
            if last_bracket:
                last_bracket.next = bracket
            last_bracket = bracket
            if self.root_bracket is None:
                self.root_bracket = bracket

    def print_table(self):
        bracket = self.root_bracket
        while bracket.next:
            print((bracket.start, bracket.end, bracket.marginal, bracket.cumulative))
            if not bracket.next:
                break
            bracket = bracket.next

    def calculate_tax(self, amount):
        net_amount = max(amount - self.deduction, 0)
        # print(f"{net_amount=}")
        # print(f"{amount=}")
        # print(f"{self.deduction=}")
        bracket = self.root_bracket
        while bracket.end and net_amount > bracket.end:
            if bracket.next:
                bracket = bracket.next
            else:
                break
        # print(bracket)
        # print(bracket.cumulative, bracket.partial_bracket_cost(net_amount))
        return bracket.cumulative + bracket.partial_bracket_cost(net_amount)


class CapitalTaxTable(TaxTable):
    def calculate_tax(self, amount, offset=0):
        if offset > self.deduction:
            return amount * 0.15
        if amount + offset < self.deduction:
            return 0
        return (amount - (self.deduction - offset)) * 0.15


FED_TAX_TABLE = TaxTable([FED_TAX_RAW], FED_STANDARD_DEDUCTION)
STATE_TAX_TABLE = TaxTable([STATE_TAX_RAW, LOCAL_TAX_RAW], STATE_STANDARD_DEDUCTION)
CAPITAL_TAX_TABLE = CapitalTaxTable([CAPITAL_TAX_RAW], CAPITAL_STANDARD_DEDUCTION)
