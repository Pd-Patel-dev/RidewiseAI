from src.pricing.rule_based import (
    TRIP_TYPE_EMPTY_RETURN,
    TRIP_TYPE_ONE_WAY,
    TRIP_TYPE_ROUND_TRIP,
    calculate_fuel_cost,
    calculate_rule_based_fare,
    calculate_trip_miles,
)


def test_fuel_cost():
    result = calculate_fuel_cost(100, 25, 4)
    assert result == 16


def test_trip_miles_one_way():
    result = calculate_trip_miles(TRIP_TYPE_ONE_WAY, 10)
    assert result["customer_miles"] == 10
    assert result["expense_miles"] == 10


def test_trip_miles_empty_return():
    result = calculate_trip_miles(TRIP_TYPE_EMPTY_RETURN, 10)
    assert result["customer_miles"] == 10
    assert result["expense_miles"] == 20


def test_trip_miles_round_trip():
    result = calculate_trip_miles(TRIP_TYPE_ROUND_TRIP, 10)
    assert result["customer_miles"] == 20
    assert result["expense_miles"] == 20


def test_rule_based_fare_one_way():
    result = calculate_rule_based_fare(
        trip_type=TRIP_TYPE_ONE_WAY,
        one_way_miles=100,
        mpg=25,
        gas_price=4,
        tolls=10,
        airport_fee=0,
        profit_margin=0.30,
    )

    # expense miles = 100, fuel = 16, maintenance = 25, tolls = 10
    assert result["customer_miles"] == 100
    assert result["expense_miles"] == 100
    assert result["fuel_cost"] == 16
    assert result["maintenance_cost"] == 25
    assert result["total_expense"] == 51
    assert result["recommended_fare"] == 66.3
    assert result["expected_profit"] == 15.3


def test_rule_based_fare_empty_return_doubles_expense_miles():
    result = calculate_rule_based_fare(
        trip_type=TRIP_TYPE_EMPTY_RETURN,
        one_way_miles=10,
        mpg=25,
        gas_price=3.5,
        tolls=0,
        airport_fee=0,
        profit_margin=0.30,
    )

    assert result["customer_miles"] == 10
    assert result["expense_miles"] == 20
    assert result["fuel_cost"] == 2.8
