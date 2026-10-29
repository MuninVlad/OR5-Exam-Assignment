import TheWholeCode as e
import time
import itertools


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


    #more data -  3 machines, 6 orders
    data_2 = {
        'surface': {'Order1': 10, 'Order2': 20, 'Order3': 8,
                    'Order4': 15, 'Order5': 12, 'Order6': 18},
        'colour': {'Order1': 'Red', 'Order2': 'Blue', 'Order3': 'Red',
                   'Order4': 'Green', 'Order5': 'Blue', 'Order6': 'Green'},
        'deadline': {'Order1': 5, 'Order2': 15, 'Order3': 6,
                     'Order4': 12, 'Order5': 10, 'Order6': 20},
        'penalty': {'Order1': 10, 'Order2': 5, 'Order3': 3,
                    'Order4': 4, 'Order5': 6, 'Order6': 2},
        'speed': {'M1': 2.0, 'M2': 1.0, 'M3': 1.5},
        'machines': ['M1', 'M2', 'M3'],
        'setup': {('Red', 'Red'): 0, ('Blue', 'Blue'): 0, ('Green', 'Green'): 0,
                  ('Red', 'Blue'): 5, ('Blue', 'Red'): 5,
                  ('Red', 'Green'): 5, ('Green', 'Red'): 5,
                  ('Blue', 'Green'): 5, ('Green', 'Blue'): 5}
    }


    # Discrete improving search

    start_sched = e.greedy(data_2)
    start_cost = e.calculate_objective(start_sched, data_2)
    start_orders = []
    for m in start_sched:
        start_orders.extend(start_sched[m])

    t0 = time.time()
    result = e.improving_search(start_sched, data_2)
    elapsed = time.time() - t0
    result_cost = e.calculate_objective(result, data_2)
    result_orders = []
    for m in result:
        result_orders.extend(result[m])

    # TEST 3: Same orders before and after local search
    if sorted(result_orders) == sorted(start_orders):
        print("Test 3 Passed: No orders lost or duplicated by local search.")
    else:
        print("Test 3 FAILED: Orders were lost or duplicated.")

    # TEST 4: Cost never gets worse
    if result_cost <= start_cost:
        print(f"Test 4 Passed: Cost went from {start_cost} to {result_cost}.")
    else:
        print(f"Test 4 FAILED: Cost got worse ({start_cost} -> {result_cost}).")



    # TEST 5: Compare local search with an exhaustive search on mock_data
    
    mock_result = e.improving_search(mock_schedule, mock_data)
    mock_result_cost = e.calculate_objective(mock_result, mock_data)

    lowest_cost_of_all = None
    for sequence in itertools.permutations(['Order1', 'Order2']):
        sched = {'M1': list(sequence)}
        c = e.calculate_objective(sched, mock_data)
        if lowest_cost_of_all is None or c < lowest_cost_of_all:
            lowest_cost_of_all = c

    if mock_result_cost < lowest_cost_of_all:
        print("Test 5 FAILED: Local search found a cost below the lowest possible, "
              "so the objective function or the schedule is wrong.")
    elif mock_result_cost == lowest_cost_of_all:
        print(f"Test 5 Passed: Local search reached the global best ({lowest_cost_of_all}).")
    

run_validation_tests()


