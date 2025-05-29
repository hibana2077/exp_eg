import ast
import operator
from collections.abc import Callable

import numpy as np
import sympy as sp

from langflow.custom import Component
from langflow.inputs import MessageTextInput
from langflow.io import Output
from langflow.schema import Data


class CalculatorComponent(Component):
    display_name = "Calculator"
    description = "Perform basic arithmetic operations, advanced mathematical functions, and calculus operations (derivatives and integrals) on a given expression."
    icon = "calculator"

    # Cache operators dictionary as a class variable
    OPERATORS: dict[type[ast.operator], Callable] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }

    # Cache numpy functions as a class variable
    NUMPY_FUNCTIONS: dict[str, Callable] = {
        'sin': np.sin,
        'cos': np.cos,
        'tan': np.tan,
        'sqrt': np.sqrt,
        'log': np.log,
        'log10': np.log10,
        'exp': np.exp,
        'abs': np.abs,
        'floor': np.floor,
        'ceil': np.ceil,
        'round': np.round,
        'pi': lambda: np.pi,
        'e': lambda: np.e,
        'mean': np.mean,
        'sum': np.sum,
        'max': np.max,
        'min': np.min,
        'std': np.std,
        'var': np.var,
    }

    # Calculus functions using sympy
    CALCULUS_FUNCTIONS = {
        'diff': 'derivative',
        'derivative': 'derivative', 
        'integrate': 'integral',
        'integral': 'integral',
        'limit': 'limit',
    }

    inputs = [
        MessageTextInput(
            name="expression",
            display_name="Expression",
            info="The arithmetic expression to evaluate. Supports numpy functions like sin, cos, sqrt, log, etc. "
                 "For calculus: diff(f, x), integrate(f, x), integrate(f, (x, a, b)), limit(f, x, c)",
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="Data", name="result", type_=Data, method="evaluate_expression"),
    ]

    def _handle_calculus_operation(self, func_name: str, args: list) -> str:
        """Handle calculus operations using sympy."""
        if func_name in ['diff', 'derivative']:
            if len(args) < 2:
                raise ValueError("Derivative requires function and variable: diff(f, x)")
            
            expr_str = args[0] if isinstance(args[0], str) else str(args[0])
            var_str = args[1] if isinstance(args[1], str) else str(args[1])
            
            # Create sympy symbols and expression
            var = sp.Symbol(var_str)
            expr = sp.sympify(expr_str)
            
            # Calculate derivative
            result = sp.diff(expr, var)
            return str(result)
            
        elif func_name in ['integrate', 'integral']:
            if len(args) < 2:
                raise ValueError("Integration requires function and variable: integrate(f, x) or integrate(f, (x, a, b))")
            
            expr_str = args[0] if isinstance(args[0], str) else str(args[0])
            
            # Handle definite vs indefinite integral
            if len(args) == 2:
                # Indefinite integral
                var_str = args[1] if isinstance(args[1], str) else str(args[1])
                var = sp.Symbol(var_str)
                expr = sp.sympify(expr_str)
                result = sp.integrate(expr, var)
                return str(result)
            elif len(args) == 4:
                # Definite integral: integrate(f, x, a, b)
                var_str = args[1] if isinstance(args[1], str) else str(args[1])
                lower = float(args[2]) if not isinstance(args[2], str) else sp.sympify(args[2])
                upper = float(args[3]) if not isinstance(args[3], str) else sp.sympify(args[3])
                
                var = sp.Symbol(var_str)
                expr = sp.sympify(expr_str)
                result = sp.integrate(expr, (var, lower, upper))
                return str(float(result)) if result.is_number else str(result)
            else:
                raise ValueError("Invalid integration format")
                
        elif func_name == 'limit':
            if len(args) < 3:
                raise ValueError("Limit requires function, variable, and point: limit(f, x, c)")
            
            expr_str = args[0] if isinstance(args[0], str) else str(args[0])
            var_str = args[1] if isinstance(args[1], str) else str(args[1])
            point = float(args[2]) if not isinstance(args[2], str) else sp.sympify(args[2])
            
            var = sp.Symbol(var_str)
            expr = sp.sympify(expr_str)
            result = sp.limit(expr, var, point)
            return str(float(result)) if result.is_number else str(result)
        
        raise ValueError(f"Unsupported calculus operation: {func_name}")

    def _parse_calculus_expression(self, expression: str) -> str:
        """Parse and evaluate calculus expressions."""
        # Simple parser for calculus functions
        expression = expression.strip()
        
        for calc_func in self.CALCULUS_FUNCTIONS:
            if expression.startswith(f"{calc_func}("):
                # Extract function arguments
                start = expression.find('(') + 1
                end = expression.rfind(')')
                args_str = expression[start:end]
                
                # Parse arguments - simple comma splitting
                args = []
                paren_count = 0
                current_arg = ""
                
                for char in args_str:
                    if char == '(':
                        paren_count += 1
                        current_arg += char
                    elif char == ')':
                        paren_count -= 1
                        current_arg += char
                    elif char == ',' and paren_count == 0:
                        args.append(current_arg.strip())
                        current_arg = ""
                    else:
                        current_arg += char
                
                if current_arg.strip():
                    args.append(current_arg.strip())
                
                return self._handle_calculus_operation(calc_func, args)
        
        # If not a calculus function, fall back to regular evaluation
        return None

    def _eval_expr(self, node: ast.AST) -> float:
        """Evaluate an AST node recursively."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int | float):
                return float(node.value)
            error_msg = f"Unsupported constant type: {type(node.value).__name__}"
            raise TypeError(error_msg)
        if isinstance(node, ast.Num):  # For backwards compatibility
            if isinstance(node.n, int | float):
                return float(node.n)
            error_msg = f"Unsupported number type: {type(node.n).__name__}"
            raise TypeError(error_msg)

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.OPERATORS:
                error_msg = f"Unsupported binary operator: {op_type.__name__}"
                raise TypeError(error_msg)

            left = self._eval_expr(node.left)
            right = self._eval_expr(node.right)
            return self.OPERATORS[op_type](left, right)

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in self.NUMPY_FUNCTIONS:
                    args = [self._eval_expr(arg) for arg in node.args]
                    if func_name in ['pi', 'e'] and not args:
                        return self.NUMPY_FUNCTIONS[func_name]()
                    if args:
                        return float(self.NUMPY_FUNCTIONS[func_name](*args))
                    else:
                        error_msg = f"Function {func_name} requires arguments"
                        raise ValueError(error_msg)
                else:
                    error_msg = f"Unsupported function: {func_name}"
                    raise TypeError(error_msg)

        if isinstance(node, ast.Name):
            if node.id == 'pi':
                return np.pi
            elif node.id == 'e':
                return np.e
            else:
                error_msg = f"Unsupported variable: {node.id}"
                raise TypeError(error_msg)

        error_msg = f"Unsupported operation or expression type: {type(node).__name__}"
        raise TypeError(error_msg)

    def evaluate_expression(self) -> Data:
        """Evaluate the mathematical expression and return the result."""
        try:
            # First check if it's a calculus expression
            calculus_result = self._parse_calculus_expression(self.expression)
            if calculus_result is not None:
                self.log(f"Calculus result: {calculus_result}")
                self.status = str(calculus_result)
                return Data(data={"result": str(calculus_result)})
            
            # Fall back to regular arithmetic evaluation
            tree = ast.parse(self.expression, mode="eval")
            result = self._eval_expr(tree.body)

            formatted_result = f"{float(result):.6f}".rstrip("0").rstrip(".")
            self.log(f"Calculation result: {formatted_result}")

            self.status = formatted_result
            return Data(data={"result": formatted_result})

        except ZeroDivisionError:
            error_message = "Error: Division by zero"
            self.status = error_message
            return Data(data={"error": error_message, "input": self.expression})

        except (SyntaxError, TypeError, KeyError, ValueError, AttributeError, OverflowError) as e:
            error_message = f"Invalid expression: {e!s}"
            self.status = error_message
            return Data(data={"error": error_message, "input": self.expression})

    def build(self):
        """Return the main evaluation function."""
        return self.evaluate_expression

# test
# basic arithmetic
# 1 + 2 * 3 - 4 / 5
# numpy functions
# sin(pi / 2) + sqrt(16) - log(10)
# calculus operations
# diff(x**2 + 3*x + 2, x)
# integrate(x**2, x) or integrate(x**2, (x, 0, 1))
# limit(sin(x) / x, x, 0)