from .accounts import Accounts, IRAAccount, RothAccount, TaxableAccount
from .tax import CAPITAL_TAX_TABLE, FED_TAX_TABLE, REGULAR_TAX, STATE_TAX_TABLE

NEED_EXPENSES = 45000
WANT_EXPENSES = 10000

ACA_PREMIUMS = 15000
MEDICARE_PREMIUMS = 5000

MINIMUM_ACCOUNT_BALANCE_PERCENT = 0.1

SS_AMOUNT = 47500


class Plan:
    def portfolio(self, age):
        return {"stocks": 0.75, "bonds": 0.2, "cash": 0.05}

    def pre_tax_expenses(self, age):
        """Calculate the years expenses before tax expenses are added."""
        base_expenses = NEED_EXPENSES + WANT_EXPENSES
        if age < 65:
            return base_expenses + ACA_PREMIUMS

        expenses = base_expenses + MEDICARE_PREMIUMS
        if age >= 70:
            expenses = max(expenses - SS_AMOUNT, 0)
        return expenses

    def income_source(self, age, starting):
        """

        Returns:
            tuple: Tuple of floats that should sum to 1.  Represents what percent of
            expenses comes from which account (taxable, ira, roth)

        At present it's all or nothing, but that could change.
        """
        if age < 60:
            return (1, 0, 0)
        if (
            starting.ira.balance - self.pre_tax_expenses(age)
            > starting.net_worth * MINIMUM_ACCOUNT_BALANCE_PERCENT
        ):
            return (0, 1, 0)
        if (
            starting.taxable.balance - self.pre_tax_expenses(age)
            > starting.net_worth * MINIMUM_ACCOUNT_BALANCE_PERCENT
        ):
            return (1, 0, 0)
        return (0, 0, 1)

    def roth_conversion(self, age):
        if age < 0:
            return 20000
        return 0


class Year:
    def __init__(
        self, age: int, taxable_value: float, ira_value: float, roth_value: float
    ):
        self.processed = False
        # Age on January 1st
        self.age = age
        # assets at the beginning of the year
        self.starting = Accounts(
            TaxableAccount(taxable_value),
            IRAAccount(ira_value),
            RothAccount(roth_value),
        )
        # Assets at the end of the year
        self.ending = None

        self.stock_growth = None
        self.bond_growth = None
        self.inflation = None

        self.plan: Plan = Plan()

    @property
    def growth(self):
        if self.stock_growth is None or self.bond_growth is None:
            return None
        portfolio = self.plan.portfolio(self.age)
        growth = 0
        growth += self.stock_growth * portfolio["stocks"]
        growth += self.bond_growth * portfolio["bonds"]
        return growth

    def _calculate_taxable_income(self, expenses):
        """
        Return the amount of taxable income broken up in to capital income, and
        regular income.
        """
        regular_income = 0
        capital_income = 0

        needed_extra_income = max(expenses - (regular_income + capital_income), 0)
        source = self.plan.income_source(self.age, self.starting)
        capital_income += needed_extra_income * source[0]
        regular_income += needed_extra_income * source[1]

        capital_income, regular_income = self._adjust_for_forced_income(
            capital_income, regular_income
        )

        regular_income += self.plan.roth_conversion(self.age)
        # print(regular_income, capital_gains)
        return capital_income, regular_income

    def _adjust_for_forced_income(self, capital_income, regular_income):
        """
        Adjust the taxable income values based on the amount of forced taxable income.

        TODO: Doesn't consider roth as a location to adjust money too, from.
        """
        forced_regular_income = 0
        forced_capital_income = 0

        for acct in (self.starting.taxable, self.starting.ira):
            if acct.TAX_TYPE == REGULAR_TAX:
                forced_regular_income += acct.forced(self.age)
            else:
                forced_capital_income += acct.forced(self.age)

        if (
            capital_income < forced_capital_income
            and regular_income < forced_regular_income
        ):
            capital_income = forced_capital_income
            regular_income = forced_regular_income
        elif capital_income < forced_capital_income:
            diff = forced_capital_income - capital_income
            capital_income = forced_capital_income
            regular_income = max(regular_income - diff, 0)
        elif regular_income < forced_regular_income:
            diff = forced_regular_income - regular_income
            regular_income = forced_regular_income
            capital_income = max(capital_income - diff, 0)
        return capital_income, regular_income

    def _calculate_taxes(self, capital_gains, regular_income):
        est_fed_taxes = FED_TAX_TABLE.calculate_tax(regular_income)
        est_state_taxes = STATE_TAX_TABLE.calculate_tax(regular_income + capital_gains)
        est_capital_taxes = CAPITAL_TAX_TABLE.calculate_tax(
            capital_gains, regular_income
        )
        # print((est_fed_taxes, est_state_taxes, est_capital_taxes))
        taxes = est_fed_taxes + est_state_taxes + est_capital_taxes
        return taxes

    def taxes(self, expenses):
        """
        TODO: Return detailed tax information:
            * amount in each bracket for each type of tax
            * Marginal rate
            * total amount per tax type.
        """
        capital_gains, regular_income = self._calculate_taxable_income(expenses)
        taxes = self._calculate_taxes(capital_gains, regular_income)

        return taxes

    def __str__(self):
        return f"<Year age:{self.age}, net worth:{self.starting.net_worth}>"

    def _annual_adjustment(self, value) -> float:
        """Apply inflation adjusted growth to the passed in value"""
        return value * (1 + self.growth - self.inflation)

    def process_year(
        self, stock_growth: float, bond_growth: float, inflation: float
    ) -> "Year":
        """Do changes to transform starting values to ending values"""
        self.stock_growth = stock_growth
        self.bond_growth = bond_growth
        self.inflation = inflation
        taxable, ira, roth = (
            self._annual_adjustment(balance)
            for balance in self.starting.balances.values()
        )

        expenses = self.plan.pre_tax_expenses(self.age)
        print(f"Pre-tax Expenses: ${expenses:,}")
        taxes = expenses * 0.3
        for _ in range(7):
            taxes = self.taxes(expenses + taxes)
            # print(f"{taxes=}")
        total_expenses = expenses + taxes
        print(f"Taxes: ${taxes:,.2f}")
        print(f"Total Expenses: ${total_expenses:,.2f}")

        source = self.plan.income_source(self.age, self.starting)
        taxable -= total_expenses * source[0]
        ira -= total_expenses * source[1]
        roth -= total_expenses * source[2]

        taxable += self.starting.ira.forced(self.age)
        ira -= self.starting.ira.forced(self.age)

        ira -= self.plan.roth_conversion(self.age)
        roth += self.plan.roth_conversion(self.age)

        self.ending = Accounts(
            TaxableAccount(taxable),
            IRAAccount(ira),
            RothAccount(roth),
        )

        self.processed = True

    def get_next_year(self):
        """Create a Year object based off our ending values and age."""
        age = self.age + 1
        if not self.processed:
            raise ValueError("can only get next after this year has been processed")
        return self.__class__(age, *self.ending.balances.values())
