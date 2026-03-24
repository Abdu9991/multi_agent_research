# tasks.py - All 5 Benchmark Tasks for Multi-Agent Research System

"""
TASK DEFINITIONS
================

This file defines all 5 benchmark tasks for evaluation:
1. Budget Planning - Financial calculations with constraints
2. Data Analysis - Statistical analysis using Python
3. Mathematical Calculations - Multi-step math problems
4. Multi-Step Reasoning - Logic puzzles and decision-making
5. Chatbot Interaction - Conversational task completion

Each task creates a sequence of subtasks following the PAOR pattern:
- Planning task (Strategic Planner)
- Execution task (Tool Executor)
- Validation task (Quality Observer)
"""

from crewai import Task
from agents import strategic_planner, tool_executor, quality_observer, reflective_analyst

# ============================================================================
# TASK 1: BUDGET PLANNING
# ============================================================================

def create_budget_planning_task(customer_request: str):
    """
    Create a budget planning task with financial calculations
    
    Example:
        create_budget_planning_task(
            "I have $5000 monthly income. Allocate 30% to rent, 
            20% to food, 15% to savings, 10% to transportation."
        )
    """
    
    planning_task = Task(
        description=f"""
        Analyze this budget planning request and create a step-by-step plan:
        
        Request: {customer_request}
        
        Your plan should:
        1. Identify all budget categories mentioned
        2. List all percentage allocations
        3. Determine what calculations are needed
        4. Check for any constraints or goals
        5. Create a clear sequence of steps
        
        Output a structured plan with numbered steps.
        """,
        expected_output="A detailed plan with steps, calculations needed, and constraints identified",
        agent=strategic_planner
    )
    
    execution_task = Task(
        description="""
        Execute the budget plan using the Calculator tool:
        
        For each budget category:
        1. Calculate the exact dollar amount from the percentage
        2. Use the Calculator tool for all calculations
        3. Show your work (e.g., "30% of $5000 = 5000 * 0.30 = $1500")
        4. Create a complete budget breakdown
        5. Verify percentages add up to 100%
        
        Present results in a clear, organized format.
        """,
        expected_output="Complete budget breakdown with all amounts calculated and shown",
        agent=tool_executor,
        context=[planning_task]
    )
    
    validation_task = Task(
        description="""
        Validate the budget calculations:
        
        Check these items:
        1. Do all percentages add to 100%?
        2. Do all dollar amounts add to the total income?
        3. Are calculations mathematically correct?
        4. Are any constraints or savings goals met?
        5. Is anything missing from the budget?
        
        Report: PASS or FAIL with specific issues if any.
        """,
        expected_output="Validation report with PASS/FAIL status and any corrections needed",
        agent=quality_observer,
        context=[planning_task, execution_task]
    )
    
    return [planning_task, execution_task, validation_task]


# ============================================================================
# TASK 2: DATA ANALYSIS
# ============================================================================

def create_data_analysis_task(dataset: list, analysis_request: str):
    """
    Create a data analysis task with statistical calculations
    
    Example:
        create_data_analysis_task(
            dataset=[100, 150, 200, 175, 300, 250],
            analysis_request="Calculate mean, median, std dev, identify outliers"
        )
    """
    
    planning_task = Task(
        description=f"""
        Create a data analysis plan:
        
        Dataset: {dataset}
        Request: {analysis_request}
        
        Your plan should specify:
        1. What statistical measures to calculate
        2. How to identify outliers (use IQR method)
        3. What tools to use (DataAnalyzer, PythonExecutor, Calculator)
        4. Expected output format
        5. Any visualizations or insights needed
        
        Create a clear analysis strategy.
        """,
        expected_output="Structured analysis plan with methods and tools specified",
        agent=strategic_planner
    )
    
    execution_task = Task(
        description=f"""
        Perform statistical analysis on this dataset: {dataset}
        
        Execute the analysis plan:
        1. Use the DataAnalyzer tool to calculate statistics
        2. Calculate: mean, median, standard deviation, min, max
        3. Identify any outliers using the IQR method
        4. Document all findings clearly
        5. Provide interpretation of results
        
        Show all calculations and tools used.
        """,
        expected_output="Complete statistical analysis with all metrics calculated and outliers identified",
        agent=tool_executor,
        context=[planning_task]
    )
    
    validation_task = Task(
        description="""
        Validate the data analysis results:
        
        Check:
        1. Are statistics calculated correctly? (verify with Calculator)
        2. Is the outlier detection method appropriate?
        3. Are interpretations logical and supported by data?
        4. Are all requested analyses completed?
        5. Are there any calculation errors?
        
        Verify key calculations independently.
        """,
        expected_output="Validation report with PASS/FAIL and verification of key statistics",
        agent=quality_observer,
        context=[planning_task, execution_task]
    )
    
    return [planning_task, execution_task, validation_task]


# ============================================================================
# TASK 3: MATHEMATICAL CALCULATIONS
# ============================================================================

def create_math_calculation_task(problem: str):
    """
    Create a mathematical calculation task
    
    Example:
        create_math_calculation_task(
            "Calculate compound interest on $10,000 at 5% annual rate 
            compounded quarterly for 3 years"
        )
    """
    
    planning_task = Task(
        description=f"""
        Create a plan to solve this math problem:
        
        Problem: {problem}
        
        Your plan should:
        1. Identify the mathematical concept (geometry, finance, algebra, etc.)
        2. State the formula needed
        3. List all known variables and their values
        4. Specify the calculation steps in order
        5. Identify what tools to use (Calculator)
        
        Provide a clear mathematical solution strategy.
        """,
        expected_output="Mathematical solution plan with formula, variables, and calculation steps",
        agent=strategic_planner
    )
    
    execution_task = Task(
        description="""
        Solve the math problem step-by-step:
        
        1. State the formula you will use
        2. Identify and label all variables (e.g., P = 10000, r = 0.05)
        3. Substitute values into the formula
        4. Calculate step-by-step using the Calculator tool
        5. Show intermediate results at each step
        6. Provide the final answer with appropriate units
        
        Document every calculation clearly and show your work.
        """,
        expected_output="Complete mathematical solution with formula, substitution, step-by-step calculations, and final answer",
        agent=tool_executor,
        context=[planning_task]
    )
    
    validation_task = Task(
        description="""
        Validate the mathematical solution:
        
        Check:
        1. Is the correct formula used for this type of problem?
        2. Are all variables identified and substituted correctly?
        3. Are calculations accurate? (verify with Calculator tool)
        4. Does the final answer make sense / is it reasonable?
        5. Are units included and correct?
        
        Recalculate key steps to verify accuracy.
        """,
        expected_output="Validation report with PASS/FAIL and verification of calculations",
        agent=quality_observer,
        context=[planning_task, execution_task]
    )
    
    return [planning_task, execution_task, validation_task]


# ============================================================================
# TASK 4: MULTI-STEP REASONING
# ============================================================================

def create_reasoning_task(problem: str):
    """
    Create a multi-step reasoning/logic task
    
    Example:
        create_reasoning_task(
            "If it takes 5 machines 5 minutes to make 5 widgets, 
            how long would it take 100 machines to make 100 widgets?"
        )
    """
    
    planning_task = Task(
        description=f"""
        Analyze this reasoning problem and create a solution plan:
        
        Problem: {problem}
        
        Your plan should:
        1. Identify what the problem is really asking
        2. Recognize any tricky aspects or common misconceptions
        3. Break down the logic step-by-step
        4. Determine what calculations (if any) are needed
        5. Outline the reasoning path to the answer
        
        Think carefully about the logic before solving.
        """,
        expected_output="Logical analysis plan showing reasoning approach and potential traps to avoid",
        agent=strategic_planner
    )
    
    execution_task = Task(
        description="""
        Solve the reasoning problem using clear logic:
        
        1. State what you know from the problem (given information)
        2. Identify the key insight or pattern
        3. Work through the logic step-by-step
        4. Perform any necessary calculations (use Calculator if needed)
        5. Arrive at the answer
        6. Explain WHY this answer makes sense
        
        Be very clear about your reasoning at each step. Avoid assumptions.
        """,
        expected_output="Logical solution with clear reasoning steps, calculations if needed, and explanation",
        agent=tool_executor,
        context=[planning_task]
    )
    
    validation_task = Task(
        description="""
        Validate the logical reasoning:
        
        Check:
        1. Does the reasoning follow logically from step to step?
        2. Are there any logical fallacies or errors?
        3. Is the answer correct?
        4. Does the explanation make sense?
        5. Were any important details or edge cases missed?
        
        Point out any flaws in the logic or reasoning.
        """,
        expected_output="Validation of reasoning with PASS/FAIL and logic verification",
        agent=quality_observer,
        context=[planning_task, execution_task]
    )
    
    return [planning_task, execution_task, validation_task]


# ============================================================================
# TASK 5: CHATBOT INTERACTION / CONVERSATIONAL TASK
# ============================================================================

def create_chatbot_task(user_request: str):
    """
    Create a conversational task completion scenario
    
    Example:
        create_chatbot_task(
            "User wants to plan a 7-day vacation to Italy with $3000 budget. 
            Help create an itinerary with cost breakdown."
        )
    """
    
    planning_task = Task(
        description=f"""
        Plan how to handle this conversational request:
        
        User Request: {user_request}
        
        Your plan should:
        1. Identify what information is needed from the user
        2. List 2-3 relevant clarifying questions to ask
        3. Determine what recommendations to provide
        4. Plan the structure of the response (itinerary, recommendations, etc.)
        5. Identify any calculations needed (budget, costs, quantities)
        
        Create a conversational strategy that is helpful and complete.
        """,
        expected_output="Conversation plan with questions to ask, response structure, and calculations needed",
        agent=strategic_planner
    )
    
    execution_task = Task(
        description="""
        Complete the user's request in a conversational manner:
        
        1. Ask 2-3 important clarifying questions (if needed)
        2. Make budget-aware recommendations
        3. Create a detailed plan/itinerary/solution
        4. Calculate all costs using Calculator tool
        5. Ensure everything stays within budget constraints
        6. Present in a friendly, helpful, conversational tone
        
        Be thorough but conversational - imagine you're helping a friend.
        """,
        expected_output="Complete conversational response with questions, recommendations, detailed plan, and accurate cost breakdown",
        agent=tool_executor,
        context=[planning_task]
    )
    
    validation_task = Task(
        description="""
        Validate the conversational response:
        
        Check:
        1. Were appropriate and helpful questions asked?
        2. Are recommendations relevant and practical?
        3. Does the plan/itinerary make logical sense?
        4. Are all costs calculated correctly? (verify with Calculator)
        5. Is everything within the stated budget?
        6. Is the tone friendly and conversational (not robotic)?
        
        Assess both accuracy and user experience quality.
        """,
        expected_output="Validation with PASS/FAIL covering accuracy, completeness, and conversational quality",
        agent=quality_observer,
        context=[planning_task, execution_task]
    )
    
    return [planning_task, execution_task, validation_task]


# ============================================================================
# TASK FACTORY FUNCTION
# ============================================================================

def create_task(task_type: str, **kwargs):
    """
    Factory function to create tasks by type
    
    Args:
        task_type: Type of task ('budget', 'data', 'math', 'reasoning', 'chatbot')
        **kwargs: Task-specific parameters
        
    Returns:
        List of Task objects (planning, execution, validation)
        
    Examples:
        >>> create_task('budget', customer_request="Allocate $5000...")
        >>> create_task('data', dataset=[1,2,3], analysis_request="Calculate stats")
        >>> create_task('math', problem="Calculate area of circle...")
        >>> create_task('reasoning', problem="Logic puzzle...")
        >>> create_task('chatbot', user_request="Plan a vacation...")
    """
    task_creators = {
        'budget': create_budget_planning_task,
        'data': create_data_analysis_task,
        'math': create_math_calculation_task,
        'reasoning': create_reasoning_task,
        'chatbot': create_chatbot_task,
    }
    
    if task_type not in task_creators:
        raise ValueError(
            f"Unknown task type: {task_type}. "
            f"Available types: {list(task_creators.keys())}"
        )
    
    return task_creators[task_type](**kwargs)


# ============================================================================
# TASK EXAMPLES FOR TESTING
# ============================================================================

def get_example_tasks():
    """
    Get example tasks for each type (useful for testing)
    
    Returns:
        Dictionary with example tasks for each type
    """
    examples = {
        'budget': {
            'customer_request': """
            I have $5000 monthly income. Please allocate:
            - 30% to rent
            - 20% to food
            - 15% to savings
            - 10% to transportation
            - 25% to other expenses (utilities, entertainment, etc.)
            """
        },
        'data': {
            'dataset': [100, 150, 200, 175, 300, 250, 180, 190, 210, 500],
            'analysis_request': 'Calculate mean, median, standard deviation, and identify outliers'
        },
        'math': {
            'problem': 'Calculate the area of a circle with radius 5 cm. Use pi = 3.14159'
        },
        'reasoning': {
            'problem': '''
            If it takes 5 machines 5 minutes to make 5 widgets,
            how long would it take 100 machines to make 100 widgets?
            Explain your reasoning.
            '''
        },
        'chatbot': {
            'user_request': '''
            User wants to plan a 3-day weekend trip to New York City with a $1000 budget.
            They enjoy museums, good food, and walking tours.
            Help create an itinerary with estimated costs.
            '''
        }
    }
    return examples


# ============================================================================
# TESTING AND DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("TASK DEFINITIONS - ALL 5 BENCHMARK TASKS")
    print("="*80)
    
    # Get example tasks
    examples = get_example_tasks()
    
    # Display information about each task type
    task_info = {
        'budget': {
            'name': 'Budget Planning',
            'description': 'Financial calculations with percentage allocations',
            'tools_used': ['Calculator'],
            'agents': ['Planner', 'Executor', 'Observer']
        },
        'data': {
            'name': 'Data Analysis',
            'description': 'Statistical analysis with outlier detection',
            'tools_used': ['DataAnalyzer', 'Calculator'],
            'agents': ['Planner', 'Executor', 'Observer']
        },
        'math': {
            'name': 'Mathematical Calculations',
            'description': 'Multi-step math problems with formulas',
            'tools_used': ['Calculator'],
            'agents': ['Planner', 'Executor', 'Observer']
        },
        'reasoning': {
            'name': 'Multi-Step Reasoning',
            'description': 'Logic puzzles and critical thinking',
            'tools_used': ['Calculator (optional)'],
            'agents': ['Planner', 'Executor', 'Observer']
        },
        'chatbot': {
            'name': 'Chatbot Interaction',
            'description': 'Conversational task completion',
            'tools_used': ['Calculator'],
            'agents': ['Planner', 'Executor', 'Observer']
        }
    }
    
    print("\nAVAILABLE TASK TYPES:")
    print("-" * 80)
    
    for task_type, info in task_info.items():
        print(f"\n{info['name'].upper()} ('{task_type}')")
        print(f"  Description: {info['description']}")
        print(f"  Tools Used: {', '.join(info['tools_used'])}")
        print(f"  Agents: {', '.join(info['agents'])}")
        print(f"  Example: {list(examples[task_type].keys())[0]} = ...")
    
    print("\n" + "="*80)
    print("USAGE EXAMPLES:")
    print("="*80)
    
    print("""
# Create a budget planning task
tasks = create_task('budget', 
    customer_request="Allocate $5000: 30% rent, 20% food, 15% savings")

# Create a data analysis task
tasks = create_task('data',
    dataset=[10, 20, 30, 40, 50, 100],
    analysis_request="Calculate statistics and identify outliers")

# Create a math task
tasks = create_task('math',
    problem="Calculate compound interest on $10,000 at 5% for 3 years")

# Create a reasoning task  
tasks = create_task('reasoning',
    problem="If 3 cats catch 3 mice in 3 minutes, how long for 100 cats?")

# Create a chatbot task
tasks = create_task('chatbot',
    user_request="Plan a 7-day Italy vacation with $3000 budget")
    """)
    
    print("\n" + "="*80)
    print(f"Total Task Types: {len(task_info)}")
    print(f"Tasks Per Type: 3 (Planning, Execution, Validation)")
    print(f"Total Tasks: {len(task_info) * 3} = 15 tasks")
    print("="*80)
    
    # Test creating one task
    print("\nTESTING: Creating a sample math task...")
    try:
        test_tasks = create_task('math', problem="Calculate 2+2")
        print(f"✓ Successfully created {len(test_tasks)} tasks")
        print(f"  1. {test_tasks[0].agent.role}")
        print(f"  2. {test_tasks[1].agent.role}")
        print(f"  3. {test_tasks[2].agent.role}")
        print("\n✓ All task functions are working correctly!")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*80)
    print("READY FOR DEPLOYMENT!")
    print("="*80)