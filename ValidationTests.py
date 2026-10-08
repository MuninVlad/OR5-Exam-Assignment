import ExamAssignment as e

def run_validation_tests():

    # tiny, fake dataset where we know the math by hand.
    mock_data = {
        'surface': {'Order1': 10, 'Order2': 20},
        'colour': {'Order1': 'Red', 'Order2': 'Blue'},
        'deadline': {'Order1': 5, 'Order2': 15},
        'penalty': {'Order1': 10, 'Order2': 5},
        'speed': {'M1': 2.0},  # Machine 1 processes 2 surface units per minute
        'machines': ['M1'],
        'setup': {('Red', 'Blue'): 5} # 5 minutes to switch from Red to Blue
    }
    # Fake schedule
    mock_schedule = {'M1': ['Order1', 'Order2']}

    # Math calculation by hand:
    # Order1: starts at 0, proc = 10/2 = 5, ends at 5. Lateness = 0. Cost = 0.
    # Order2: setup = 5, starts at 5+5 = 10, proc = 20/2 = 10, ends at 20. 
    #         Lateness = max(0, 20-15) = 5. Cost = 5 lateness * 5 penalty = 25.
    # Total expected cost = 25.


    #--------------------------------------------------------------------

    # TEST 1: Objective Function Calculation Validation
    
    calculated_cost = e.calculate_objective(mock_schedule, mock_data)
    if calculated_cost == 25:
        print("Test 1 Passed: Objective function calculated exactly 25.")
    else:
        print(f"Test 1 FAILED: Expected cost to be 25, but got {calculated_cost}.")
    


    
    # TEST 2: Schedule Validity (No missing or duplicate orders)
    
    # run the greedy heuristic on the mock data to see if it generates a legal schedule.
    greedy_sched = e.greedy(mock_data)

    scheduled_orders = []
    for m in greedy_sched:
        scheduled_orders.extend(greedy_sched[m])
        
    # Did it schedule exactly 2 orders?
    if len(scheduled_orders) == 2:
        print("Test 2a Passed: Schedule contains the correct number of orders.")
    else:
        print(f"Test 2a FAILED: Schedule should have 2 orders, but has {len(scheduled_orders)}.")
        
    # orders are present
    if 'Order1' in scheduled_orders and 'Order2' in scheduled_orders:
        print("Test 2b Passed: All specific orders are present in the schedule.")
    else:
        print("Test 2b FAILED: One or more orders are missing from the schedule.")

    # no duplicate orders
    # A 'set' automatically removes duplicates. If the length changes, duplicates existed.
    if len(set(scheduled_orders)) == len(scheduled_orders):
        print("Test 2c Passed: No duplicate orders found in the schedule.")
    else:
        print("Test 2c FAILED: Duplicate orders were scheduled.")

    
