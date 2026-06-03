"""
A tiny numeric addition helper with input validation.

This module includes a function `add` that takes two numeric inputs and returns their sum. It raises a `TypeError` if either input is not numeric.
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
