import os
import argparse
from typing import Dict, List
from collections import defaultdict

from dateutil.relativedelta import relativedelta
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from dataclasses import dataclass
from splitwise import Splitwise
import pandas as pd

@dataclass
class Expense:
    to_user: str
    from_user: str
    cost: str

def calculate_expenses(expense):
    return Expense(
        to_user = expense.repayments[0].toUser,
        from_user = expense.repayments[0].fromUser,
        cost = expense.cost
        )

def set_of_expenses(expenses, labels = {}):
    monthly = defaultdict(float)
    for i in expenses:

        if i.deleted_at or len(i.repayments) < 1 or i.payment:
            continue
        else:
            expense = calculate_expenses(i)
            lookup_name = labels[expense.to_user] if expense.to_user in labels else expense.to_user
            monthly[lookup_name] += float(expense.cost) / 2
    return monthly

def parse_names(env_lookup):
    pairs = env_lookup.split(',')
    return {int(pairs[i]): pairs[i + 1] for i in range(0, len(pairs), 2)}

def calculate_month_numbers(start_date, end_date):
    date_list = []
    current_date = start_date
    while current_date < end_date:
        date_list.append(current_date.strftime("%Y-%m"))
        current_date += relativedelta(months=1)
    return date_list

def main():
    """
        Main function to process Splitwise expenses for a specified date range.

        Command Line Arguments:
            --from_date: Start date in the format 'YYYY-MM'.
            --to_date: End date in the format 'YYYY-MM'.
    """
    parser = argparse.ArgumentParser(description="Process Splitwise expenses for a specified date range.")

    parser.add_argument("--from_date", required=True, help="Start date in the format 'YYYY-MM'")
    parser.add_argument("--to_date", required=True, help="End date in the format 'YYYY-MM'")

    args = parser.parse_args()

    try:
        from_date = datetime.strptime(args.from_date, "%Y-%m")
        to_date = datetime.strptime(args.to_date, "%Y-%m")
    except ValueError:
        print("Invalid date format. Please use 'YYYY-MM' format.")
        return

    dotenv_path = Path('.env')
    load_dotenv(dotenv_path=dotenv_path)

    consumer_key = os.getenv('CONSUMER_KEY')
    consumer_secret = os.getenv('CONSUMER_SECRET')
    api_key = os.getenv('API_KEY')
    labels = parse_names(os.getenv('LOOKUP'))

    sObj = Splitwise(consumer_key, consumer_secret, api_key=api_key)

    results = []
    for month in calculate_month_numbers(from_date, to_date):
        expenses = sObj.getExpenses(dated_after=f'{month}-01', dated_before=f'{month}-31')
        result = set_of_expenses(expenses, labels=labels)
        result['month'] = month
        results.append(result)
    df = pd.DataFrame.from_records(results)
    df.to_csv("expenses.csv")

if __name__ == "__main__":
    """ python main.py --from_date="2021-10" --to_date="2023-10 """
    main()

