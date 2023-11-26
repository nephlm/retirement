import json
import random
from pathlib import Path

from .year import Year

MAX_AGE = 97
RUNS_PER_SIMULATION = 1500

ALL_INFLATION = json.loads((Path.cwd() / "retirement/inflation_list.json").read_text())
ALL_STOCK_GROWTH = json.loads(
    (Path.cwd() / "retirement/stock_returns.json").read_text()
)
ALL_BOND_GROWTH = json.loads((Path.cwd() / "retirement/bond_returns.json").read_text())


class Run:
    def __init__(
        self, age: int, taxable_value: float, ira_value: float, roth_value: float
    ):
        self.first_year = Year(age, taxable_value, ira_value, roth_value)
        self.last_year = None

    @property
    def is_success(self):
        if self.ending:
            return self.ending.net_worth > 0
        return None

    @property
    def starting(self):
        return self.first_year.starting

    @property
    def ending(self):
        if self.last_year:
            return self.last_year.ending
        return None

    def process(self):
        curr_year = self.first_year
        while curr_year.age < MAX_AGE:
            curr_year.process_year(
                self.get_stock_growth(), self.get_bond_growth(), self.get_inflation()
            )
            curr_year = curr_year.get_next_year()
            # if curr_year.ending:
            # print(f"{curr_year.age} - ${curr_year.ending.net_worth:,}")
            self.last_year = curr_year
        self.last_year.process_year(
            self.get_stock_growth(), self.get_bond_growth(), self.get_inflation()
        )

        print(f"{self.last_year.ending.net_worth=:,}")

    def get_stock_growth(self):
        return random.choice(ALL_STOCK_GROWTH) / 100

    def get_bond_growth(self):
        return random.choice(ALL_BOND_GROWTH) / 100

    def get_inflation(self):
        return random.choice(ALL_INFLATION) / 100


class MonteCarlo:
    def __init__(self, age, taxable, ira, roth) -> None:
        self.starting_age = age
        self.starting_taxable = taxable
        self.starting_ira = ira
        self.starting_roth = roth

        self.runs = []
        self.sorted_runs = []
        self.failures = 0

        self.reset()

    def reset(self):
        self.runs = []
        self.sorted_runs = []
        self.failures = 0

    def start(self):
        self.reset()
        for _ in range(RUNS_PER_SIMULATION):
            run = Run(
                self.starting_age,
                self.starting_taxable,
                self.starting_ira,
                self.starting_roth,
            )
            run.process()
            if not run.is_success:
                self.failures += 1
            self.runs.append(run)

    def get_nth_percentile_run(self, percentile):
        if not self.runs:
            return None
        if not self.sorted_runs:
            self.sorted_runs = sorted(self.runs, key=lambda a: a.ending.net_worth)

        index = int(percentile * len(self.runs) / 100)
        return self.sorted_runs[index]

    def report(self):
        print("=======================================")
        print(f"number of runs: {len(self.runs)}")
        print(f"Failures: {self.failures} [{(self.failures/len(self.runs)*100):.2f}%]")
        tenth_percentile_run = self.get_nth_percentile_run(10)
        median_run = self.get_nth_percentile_run(50)
        ninetieth_percentile_run = self.get_nth_percentile_run(90)
        print(f"Median Net Worth: ${median_run.ending.net_worth:,}")
        print(f"10% Net Worth: ${tenth_percentile_run.ending.net_worth:,}")
        print(f"90% Net Worth: ${ninetieth_percentile_run.ending.net_worth:,}")
