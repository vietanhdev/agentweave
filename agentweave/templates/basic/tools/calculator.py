"""
Calculator tool for performing basic mathematical operations.
"""

import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from tools.registry import register_tool

logger = logging.getLogger(__name__)

# Debug print
print("Loading calculator.py module!")


class CalculatorInput(BaseModel):
    """Input for the calculator tool."""

    operation: str = Field(
        ...,
        description="The mathematical operation to perform. One of: add, subtract, multiply, divide",
    )
    a: float = Field(..., description="The first number")
    b: float = Field(..., description="The second number")


@register_tool
class CalculatorTool(BaseTool):
    """Tool that adds, subtracts, multiplies, or divides two numbers."""

    name: str = "calculator"
    description: str = (
        "A calculator for performing basic math operations (add, subtract, multiply, divide)"
    )
    args_schema: type[BaseModel] = CalculatorInput

    def _run(self, operation: str, a: float, b: float, **kwargs) -> float | str:
        """Execute the calculator."""
        operation = operation.lower().strip()

        try:
            if operation == "add":
                return a + b
            elif operation == "subtract":
                return a - b
            elif operation == "multiply":
                return a * b
            elif operation == "divide":
                if b == 0:
                    return "Error: Division by zero"
                return a / b
            else:
                return f"Error: Unsupported operation '{operation}'. Please use one of: add, subtract, multiply, divide"
        except Exception as e:
            logger.error(f"Error in calculator: {str(e)}")
            return f"Error: {str(e)}"

    async def _arun(self, operation: str, a: float, b: float, **kwargs) -> float | str:
        """Execute the calculator asynchronously."""
        return self._run(operation, a, b, **kwargs)


# Print registration confirmation
print(f"Calculator tool registered with name: {CalculatorTool().name}")

# Example of using the tool
if __name__ == "__main__":
    calculator = CalculatorTool()
    result = calculator.invoke({"operation": "add", "a": 2, "b": 2})
    print(f"2 + 2 = {result}")
