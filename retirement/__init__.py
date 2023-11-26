import argparse

from retirement.simulation import MonteCarlo, Run


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("age", type=int, help="Age at start of retirement.")
    parser.add_argument(
        "taxable", type=float, help="value of taxable retirement account."
    )
    parser.add_argument("ira", type=float, help="value of ira/401K retirement account.")
    parser.add_argument("roth", type=float, help="value of roth retirement account.")
    return parser


def run():
    # print(args)

    parser = get_parser()
    args = parser.parse_args()

    run1 = Run(args.age, args.taxable, args.ira, args.roth)
    run1.process()
    print(run1.is_success)

    # year = Year(args.age, args.taxable, args.ira, args.roth)
    # year.process_year(0.07, 0.02)


def monte_carlo():
    parser = get_parser()
    args = parser.parse_args()

    mc = MonteCarlo(args.age, args.taxable, args.ira, args.roth)
    mc.start()
    mc.report()
