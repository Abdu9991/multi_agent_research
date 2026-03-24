# Copy this entire block and paste into PowerShell:

# tools.py - All 4 Custom Tools
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field, PrivateAttr
import ast
import operator
import math
import statistics
import json
from datetime import datetime
import sys
from io import StringIO
import contextlib

class CalculatorInput(BaseModel):
    expression: str = Field(..., description="Mathematical expression to evaluate")

class CalculatorTool(BaseTool):
    name: str = "Calculator"
    description: str = "Performs safe mathematical calculations. Supports: +, -, *, /, **, sqrt, sin, cos, tan, log, exp, pi, e"
    args_schema: Type[BaseModel] = CalculatorInput
    
    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    
    _functions = {
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'abs': abs,
        'round': round,
    }
    
    _constants = {
        'pi': math.pi,
        'e': math.e,
    }
    
    def _run(self, expression: str) -> str:
        try:
            expression = expression.strip()
            node = ast.parse(expression, mode='eval').body
            result = self._eval_node(node)
            
            if isinstance(result, float):
                if result.is_integer():
                    return str(int(result))
                else:
                    return f"{result:.6f}".rstrip('0').rstrip('.')
            else:
                return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _eval_node(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self._operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            return self._operators[type(node.op)](operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name not in self._functions:
                raise ValueError(f"Function '{func_name}' not allowed")
            args = [self._eval_node(arg) for arg in node.args]
            return self._functions[func_name](*args)
        elif isinstance(node, ast.Name):
            if node.id in self._constants:
                return self._constants[node.id]
            else:
                raise ValueError(f"Variable '{node.id}' not defined")
        else:
            raise ValueError(f"Unsupported operation")

class PythonExecutorInput(BaseModel):
    code: str = Field(..., description="Python code to execute")

class PythonExecutorTool(BaseTool):
    name: str = "PythonExecutor"
    description: str = "Executes Python code safely. Available: math, statistics"
    args_schema: Type[BaseModel] = PythonExecutorInput
    
    def _run(self, code: str) -> str:
        try:
            restricted_globals = {
                '__builtins__': {
                    'print': print, 'len': len, 'range': range, 'sum': sum,
                    'min': min, 'max': max, 'abs': abs, 'round': round,
                },
                'math': math,
                'statistics': statistics,
            }
            
            output_buffer = StringIO()
            with contextlib.redirect_stdout(output_buffer):
                exec(code, restricted_globals)
            
            output = output_buffer.getvalue()
            return output.strip() if output else "Code executed successfully"
        except Exception as e:
            return f"Error: {type(e).__name__}: {str(e)}"

class DataAnalysisInput(BaseModel):
    data: list[float] = Field(..., description="List of numbers")
    analysis_type: str = Field(default="all", description="Type of analysis")

class DataAnalysisTool(BaseTool):
    name: str = "DataAnalyzer"
    description: str = "Performs statistical analysis on data"
    args_schema: Type[BaseModel] = DataAnalysisInput
    
    def _run(self, data: list[float], analysis_type: str = "all") -> str:
        try:
            data = [float(x) for x in data]
            if len(data) == 0:
                return "Error: No data"
            
            mean_val = statistics.mean(data)
            median_val = statistics.median(data)
            std_val = statistics.stdev(data) if len(data) > 1 else 0
            
            return f"Mean: {mean_val:.2f}, Median: {median_val:.2f}, Std Dev: {std_val:.2f}, Min: {min(data)}, Max: {max(data)}"
        except Exception as e:
            return f"Error: {str(e)}"

class ReasoningLoggerInput(BaseModel):
    step: str = Field(..., description="Current step")
    reasoning: str = Field(..., description="Reasoning explanation")
    agent: str = Field(default="Unknown", description="Agent name")

class ReasoningLoggerTool(BaseTool):
    name: str = "ReasoningLogger"
    description: str = "Logs reasoning steps for transparency"
    args_schema: Type[BaseModel] = ReasoningLoggerInput
    _logs: list = PrivateAttr(default_factory=list)
    
    def _run(self, step: str, reasoning: str, agent: str = "Unknown") -> str:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "step": step,
            "reasoning": reasoning,
        }
        self._logs.append(log_entry)
        print(f"[{agent}] {step}: {reasoning}")
        return f"Logged: {step}"

calculator_tool = CalculatorTool()
python_executor_tool = PythonExecutorTool()
data_analysis_tool = DataAnalysisTool()
reasoning_logger_tool = ReasoningLoggerTool()

if __name__ == "__main__":
    print("Testing Calculator:", calculator_tool._run("2 + 2"))
    print("Testing Data Analyzer:", data_analysis_tool._run([1,2,3,4,5], "all"))
    print("All tools work!")
   
