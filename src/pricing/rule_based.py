def calculate_fuel_cost(miles: float, mpg: float, gas_price: float) -> float:
    return (miles / mpg) * gas_price


def calculate_time_cost(trip_minutes: float, waiting_minutes: float, hourly_rate: float) -> float:
    total_hours = (trip_minutes + waiting_minutes) / 60
    return total_hours * hourly_rate


def calculate_maintenance_cost(miles: float, maintenance_rate: float = 0.25) -> float:
    return miles * maintenance_rate


def calculate_total_cost(
    fuel_cost: float,
    time_cost: float,
    maintenance_cost: float,
    tolls: float,
    airport_fee: float
) -> float:
    return fuel_cost + time_cost + maintenance_cost + tolls + airport_fee


def calculate_recommended_fare(total_cost: float, profit_margin: float) -> float:
    return total_cost * (1 + profit_margin)


def calculate_rule_based_fare(
    miles: float,
    mpg: float,
    gas_price: float,
    trip_minutes: float,
    waiting_minutes: float,
    hourly_rate: float,
    tolls: float,
    airport_fee: float,
    profit_margin: float
) -> dict:
    fuel_cost = calculate_fuel_cost(miles, mpg, gas_price)
    time_cost = calculate_time_cost(trip_minutes, waiting_minutes, hourly_rate)
    maintenance_cost = calculate_maintenance_cost(miles)
    total_cost = calculate_total_cost(
        fuel_cost,
        time_cost,
        maintenance_cost,
        tolls,
        airport_fee
    )
    recommended_fare = calculate_recommended_fare(total_cost, profit_margin)
    profit = recommended_fare - total_cost

    return {
        "fuel_cost": round(fuel_cost, 2),
        "time_cost": round(time_cost, 2),
        "maintenance_cost": round(maintenance_cost, 2),
        "total_cost": round(total_cost, 2),
        "recommended_fare": round(recommended_fare, 2),
        "expected_profit": round(profit, 2)
    }