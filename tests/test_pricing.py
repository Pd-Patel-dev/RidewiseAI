from src.pricing.rule_based import calculate_fuel_cost, calculate_rule_based_fare


def test_fuel_cost():
    result = calculate_fuel_cost(100, 25, 4)
    assert result == 16


def test_rule_based_fare():
    result = calculate_rule_based_fare(
        miles=100,
        mpg=25,
        gas_price=4,
        trip_minutes=120,
        waiting_minutes=0,
        hourly_rate=25,
        tolls=10,
        airport_fee=0,
        profit_margin=0.30
    )

    assert result["fuel_cost"] == 16
    assert result["time_cost"] == 50
    assert result["total_cost"] > 0
    assert result["recommended_fare"] > result["total_cost"]