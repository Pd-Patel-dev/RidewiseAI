def calculate_actual_profit(fare_charged: float, total_expense: float) -> float:
    """How much you keep after trip expenses when the customer pays a set fare."""
    return round(fare_charged - total_expense, 2)


def calculate_profit_per_expense_mile(actual_profit: float, expense_miles: float) -> float:
    """Profit earned for each mile the car actually drove."""
    if expense_miles <= 0:
        return 0.0
    return round(actual_profit / expense_miles, 2)


def calculate_profit_per_customer_mile(actual_profit: float, customer_miles: float) -> float:
    """Profit earned for each mile the customer is paying for."""
    if customer_miles <= 0:
        return 0.0
    return round(actual_profit / customer_miles, 2)
