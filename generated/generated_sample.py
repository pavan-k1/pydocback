"""Provides basic mathematical utility functions.

Includes addition, even number check, and factorial calculation.
"""

def add_numbers(a, b):
    """Add two numbers together.

    Args:
        a (int | float): The first number.
        b (int | float): The second number.

    Returns:
        int | float: The sum of `a` and `b`.
    """
    return a + b

def is_even(number):
    """Check if a number is even.

    Args:
        number (int): The integer to evaluate.

    Returns:
        bool: True if the number is even, False otherwise.
    """
    return number % 2 == 0

def factorial(n):
    """Calculate the factorial of a non-negative integer.

    The factorial of an integer `n` is the product of all positive integers
    less than or equal to `n`. By definition, the factorial of 0 is 1.

    Args:
        n (int): The non-negative integer for which to calculate the factorial.

    Returns:
        int: The factorial of `n`.
    """
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result