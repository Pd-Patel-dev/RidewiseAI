TRIP_TYPE_ONE_WAY = "One-way"
TRIP_TYPE_EMPTY_RETURN = "One-way + empty return"
TRIP_TYPE_ROUND_TRIP = "Round trip with customer"

TRIP_TYPES = [
    TRIP_TYPE_ONE_WAY,
    TRIP_TYPE_EMPTY_RETURN,
    TRIP_TYPE_ROUND_TRIP,
]


def calculate_fuel_cost(expense_miles: float, mpg: float, gas_price: float) -> float:
    return (expense_miles / mpg) * gas_price


def calculate_maintenance_cost(
    expense_miles: float, maintenance_rate: float = 0.25
) -> float:
    return expense_miles * maintenance_rate


def calculate_total_expense(
    fuel_cost: float,
    maintenance_cost: float,
    tolls: float,
    airport_fee: float,
) -> float:
    return fuel_cost + maintenance_cost + tolls + airport_fee


def calculate_recommended_fare(total_expense: float, profit_margin: float) -> float:
    return total_expense * (1 + profit_margin)


def calculate_trip_miles(trip_type: str, one_way_miles: float) -> dict:
    """Convert one-way distance into customer miles and expense miles."""
    if trip_type == TRIP_TYPE_ONE_WAY:
        customer_miles = one_way_miles
        expense_miles = one_way_miles
    elif trip_type == TRIP_TYPE_EMPTY_RETURN:
        customer_miles = one_way_miles
        expense_miles = one_way_miles * 2
    elif trip_type == TRIP_TYPE_ROUND_TRIP:
        customer_miles = one_way_miles * 2
        expense_miles = one_way_miles * 2
    else:
        raise ValueError(f"Unknown trip type: {trip_type}")

    return {
        "customer_miles": customer_miles,
        "expense_miles": expense_miles,
    }


def calculate_rule_based_fare(
    trip_type: str,
    one_way_miles: float,
    mpg: float,
    gas_price: float,
    tolls: float,
    airport_fee: float,
    profit_margin: float,
    trip_minutes: float = 0,
    waiting_minutes: float = 0,
) -> dict:
    """
    Calculate a recommended fare for an owner-driver.

    Fuel and maintenance use expense_miles (miles the car actually drives).
    trip_minutes and waiting_minutes are kept for future ML/data tracking only.
    """
    trip_miles = calculate_trip_miles(trip_type, one_way_miles)
    customer_miles = trip_miles["customer_miles"]
    expense_miles = trip_miles["expense_miles"]

    fuel_cost = calculate_fuel_cost(expense_miles, mpg, gas_price)
    maintenance_cost = calculate_maintenance_cost(expense_miles)
    total_expense = calculate_total_expense(
        fuel_cost,
        maintenance_cost,
        tolls,
        airport_fee,
    )
    recommended_fare = calculate_recommended_fare(total_expense, profit_margin)
    expected_profit = recommended_fare - total_expense

    return {
        "trip_type": trip_type,
        "one_way_miles": round(one_way_miles, 2),
        "customer_miles": round(customer_miles, 2),
        "expense_miles": round(expense_miles, 2),
        "fuel_cost": round(fuel_cost, 2),
        "maintenance_cost": round(maintenance_cost, 2),
        "total_expense": round(total_expense, 2),
        "recommended_fare": round(recommended_fare, 2),
        "expected_profit": round(expected_profit, 2),
        "trip_minutes": trip_minutes,
        "waiting_minutes": waiting_minutes,
    }
