
def calculate_sum(a, b):
    """Простая функция сложения"""
    return a + b

def factorial(n):
    """Вычисление факториала"""
    if n == 0:
        return 1
    return n * factorial(n - 1)

def main():
    """Основная функция"""
    result1 = calculate_sum(5, 3)
    result2 = factorial(5)

    print(f"Sum: {result1}")
    print(f"Factorial: {result2}")

    return {
        "sum_result": result1,
        "factorial_result": result2
    }

if __name__ == "__main__":
    main()
