import re

class CalculatorError(Exception):
    pass

def parse_and_calculate(question: str) -> float:
    q = question.lower().strip()
    patterns = [
        (r'(?:what is|calculate|compute|find)?\s*([\d.]+)\s*(plus|add|\+|minus|subtract|\-|times|multiply|\*|x|divided by|divide|/)\s*([\d.]+)', None),
        (r'add\s*([\d.]+)\s*(and|to)\s*([\d.]+)', 'add'),
        (r'subtract\s*([\d.]+)\s*from\s*([\d.]+)', 'subtract_reverse'),
        (r'multiply\s*([\d.]+)\s*(and|by)\s*([\d.]+)', 'multiply'),
        (r'divide\s*([\d.]+)\s*by\s*([\d.]+)', 'divide'),
    ]
    for pat, forced_op in patterns:
        m = re.search(pat, q)
        if m:
            if forced_op:
                if forced_op == 'add':
                    return float(m.group(1)) + float(m.group(3))
                elif forced_op == 'subtract_reverse':
                    return float(m.group(2)) - float(m.group(1))
                elif forced_op == 'multiply':
                    return float(m.group(1)) * float(m.group(3))
                elif forced_op == 'divide':
                    return float(m.group(1)) / float(m.group(3))
            else:
                a = float(m.group(1))
                op = m.group(2)
                b = float(m.group(3))
                if op in ['plus', 'add', '+']:
                    return a + b
                elif op in ['minus', 'subtract', '-']:
                    return a - b
                elif op in ['times', 'multiply', '*', 'x']:
                    return a * b
                elif op in ['divided by', 'divide', '/']:
                    return a / b
    m = re.match(r'([\d.]+)\s*([+\-*/x])\s*([\d.]+)', q)
    if m:
        a, op, b = float(m.group(1)), m.group(2), float(m.group(3))
        if op == '+': return a + b
        if op == '-': return a - b
        if op in ['*', 'x']: return a * b
        if op == '/': return a / b
    raise CalculatorError("Sorry, I couldn't understand the calculation.")

def is_math_question(question: str) -> bool:
    math_keywords = ['add', 'plus', 'sum', 'total', 'subtract', 'minus', 'difference', 'multiply', 'times', 'product', 'divide', 'divided', 'quotient', '+', '-', '*', 'x', '/']
    count = sum(1 for word in math_keywords if word in question.lower())
    return count > 0 or bool(re.match(r'.*\d+\s*([+\-*/x])\s*\d+', question))

def is_multi_step(question: str) -> bool:
    q = question.lower()
    math = is_math_question(q)
    nonmath_keywords = ['capital', 'who', 'when', 'where', 'why', 'how', 'name', 'explain']
    nonmath = any(word in q for word in nonmath_keywords)
    if math and nonmath:
        return True
    if not math and (' and ' in q or ',' in q or q.count('?') > 1):
        return True
    return False