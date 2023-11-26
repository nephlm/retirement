from dataclasses import dataclass

from .tax import CAPITAL_TAX, REGULAR_TAX

DIVIDEND_RATE = 0.015

RMD = {
    72: 27.4,
    73: 26.5,
    74: 25.5,
    75: 24.6,
    76: 23.7,
    77: 22.9,
    78: 22,
    79: 21.1,
    80: 20.2,
    81: 19.4,
    82: 18.5,
    83: 17.7,
    84: 16.8,
    85: 16,
    86: 15.2,
    87: 14.4,
    88: 13.7,
    89: 12.9,
    90: 12.2,
    91: 11.5,
    92: 10.8,
    93: 10.1,
    94: 9.5,
    95: 8.9,
    96: 8.4,
    97: 7.8,
    98: 7.3,
    99: 6.8,
    100: 6.4,
    101: 6,
    102: 5.6,
}


class BaseAccount:
    TAX_TYPE = REGULAR_TAX

    def __init__(self, balance) -> None:
        self.balance = balance

    def forced(self, age):
        return 0


class TaxableAccount(BaseAccount):
    TAX_TYPE = CAPITAL_TAX

    def forced(self, age):
        return self.balance * DIVIDEND_RATE


class IRAAccount(BaseAccount):
    def forced(self, age):
        if age in RMD:
            return self.balance / RMD[age]
        return 0


class RothAccount(BaseAccount):
    pass


@dataclass
class Accounts:
    taxable: TaxableAccount
    ira: IRAAccount
    roth: RothAccount

    @property
    def net_worth(self):
        return int(sum([a.balance for a in (self.taxable, self.ira, self.roth)]))

    @property
    def balances(self):
        return {
            "taxable": self.taxable.balance,
            "ira": self.ira.balance,
            "roth": self.roth.balance,
        }
