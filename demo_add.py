"""
A simple numeric addition tool with basic input checks.

This module features a function `add` that accepts two numbers, validates them to be numeric, and returns their sum. If either input is non-numeric, it raises a `TypeError`.
"""

def add(a: int | float, b: int | float) -> int | float:
    """
    Sums two numeric inputs.
    
    Args:
        a (int | float): The first number.
        b (int | float): The second number.

    Returns:
        int | float: The sum of the two numbers.

    Raises:
        TypeError: If either argument is not numeric.
    """
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError("Both arguments must be numeric")
    return a + b
