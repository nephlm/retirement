import pytest

import retirement.accounts as accounts


def test_balance():
    acct = accounts.BaseAccount(500)
    assert acct.balance == 500


def test_taxable_forced():
    acct = accounts.TaxableAccount(5000)
    assert acct.balance == 5000
    assert acct.forced(75) == 5000 * accounts.DIVIDEND_RATE


@pytest.mark.parametrize(
    "age,balance,rmd",
    [
        (75, 5000, 5000 / 24.6),
        (100, 5000, 5000 / 6.4),
        (71, 5000, 0),
        (80, 0, 0),
        (40, 5000, 0),
    ],
)
def test_ira_forced(age, balance, rmd):
    acct = accounts.IRAAccount(balance)
    assert acct.balance == balance
    assert acct.forced(age) == rmd


def test_roth_forced():
    acct = accounts.RothAccount(5000)
    assert acct.balance == 5000
    assert acct.forced(75) == 0


class TestAccounts:
    def test_basic(self):
        accts = accounts.Accounts(
            accounts.TaxableAccount(100),
            accounts.IRAAccount(200),
            accounts.RothAccount(300),
        )
        assert accts.taxable.balance == 100
        assert accts.ira.balance == 200
        assert accts.roth.balance == 300

        assert accts.net_worth == 600

    def test_balances(self):
        accts = accounts.Accounts(
            taxable=accounts.TaxableAccount(300),
            ira=accounts.IRAAccount(250),
            roth=accounts.RothAccount(130),
        )
        assert accts.taxable.balance == 300
        assert accts.ira.balance == 250
        assert accts.roth.balance == 130

        assert accts.net_worth == 680
        assert accts.balances == {"taxable": 300, "ira": 250, "roth": 130}
