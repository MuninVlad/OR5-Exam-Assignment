

import time
import pandas as pd

FILE_NAME = "PaintShop - November 2026.xlsx"   # change this line to use another dataset
EPS = 1e-6                                      # tolerance for comparing decimal numbers


def read_file(sample):
    df_orders = pd.read_excel(sample, sheet_name='Orders')
    df_machines = pd.read_excel(sample, sheet_name='Machines')
    df_setups = pd.read_excel(sample, sheet_name='Setups')

    data = {}
    data['orders'] = list(df_orders['Order'])
    data['surface'] = dict(zip(df_orders['Order'], df_orders['Surface']))
    data['colour'] = dict(zip(df_orders['Order'], df_orders['Colour']))
    data['deadline'] = dict(zip(df_orders['Order'], df_orders['Deadline']))
    data['penalty'] = dict(zip(df_orders['Order'], df_orders['Penalty']))

    data['speed'] = dict(zip(df_machines['Machine'], df_machines['Speed']))
    data['machines'] = list(df_machines['Machine'])

    data['setup'] = {}
    for i in range(len(df_setups)):
        colour_from = df_setups.iloc[i, 0]
        colour_to = df_setups.iloc[i, 1]
        setup_time = df_setups.iloc[i, 2]
        data['setup'][(colour_from, colour_to)] = setup_time

    return data



def copy_solution(solution):
    new_solution = []
    for machine_orders in solution:
        new_solution.append(machine_orders.copy())
    return new_solution


def number_of_positions(solution, source_machine, target_machine):
   
    count = len(solution[target_machine])
    if target_machine != source_machine:
        count = count + 1
    return count


def get_setup_time(previous_colour, colour, data):
    if previous_colour is None or previous_colour == colour:
        return 0
    return data['setup'][(previous_colour, colour)]


def evaluate_machine(machine_orders, m, data):
    # returns (penalty, setup time) of machine number m
    time_now = 0
    total_penalty = 0
    total_setup = 0
    previous_colour = None
    machine_name = data['machines'][m]

    for o in machine_orders:
        colour = data['colour'][o]

        setup_time = get_setup_time(previous_colour, colour, data)
        time_now = time_now + setup_time
        total_setup = total_setup + setup_time

        time_now = time_now + data['surface'][o] / data['speed'][machine_name]

        lateness = max(0, time_now - data['deadline'][o])
        total_penalty = total_penalty + data['penalty'][o] * lateness

        previous_colour = colour

    return total_penalty, total_setup


def calculate_objective(solution, data):
    # returns (total penalty, total setup time)
    total_penalty = 0
    total_setup = 0
    for m in range(len(solution)):
        machine_penalty, machine_setup = evaluate_machine(solution[m], m, data)
        total_penalty = total_penalty + machine_penalty
        total_setup = total_setup + machine_setup
    total_penalty = round(float(total_penalty), 6)
    total_setup = round(float(total_setup), 6)
    return total_penalty, total_setup


def is_better(new, old):
    # lower penalty is better, if the penalty is equal, lower setup is better
    if new[0] < old[0] - EPS:
        return True
    if abs(new[0] - old[0]) <= EPS and new[1] < old[1] - EPS:
        return True
    return False


def relocate(solution, source_machine, source_position, target_machine, target_position):

    neighbor = copy_solution(solution)
    order = neighbor[source_machine].pop(source_position)
    neighbor[target_machine].insert(target_position, order)
    return neighbor


def swap(solution, machine_1, position_1, machine_2, position_2):
    
    neighbor = copy_solution(solution)
    order_1 = neighbor[machine_1][position_1]
    order_2 = neighbor[machine_2][position_2]
    neighbor[machine_1][position_1] = order_2
    neighbor[machine_2][position_2] = order_1
    return neighbor


# greedy

def greedy(data):
    solution = []
    machine_time = []
    machine_colour = []
    for m in range(len(data['machines'])):
        solution.append([])
        machine_time.append(0)
        machine_colour.append(None)

    unassigned_orders = list(data['orders'])

    while len(unassigned_orders) > 0:
        best_key = None
        best_order = None
        best_machine = None
        best_end_time = None

        for o in unassigned_orders:
            for m in range(len(data['machines'])):
                machine_name = data['machines'][m]
                setup_time = get_setup_time(machine_colour[m], data['colour'][o], data)
                end_time = machine_time[m] + setup_time + data['surface'][o] / data['speed'][machine_name]

                lateness = max(0, end_time - data['deadline'][o])
                added_cost = lateness * data['penalty'][o]

                key = (added_cost, end_time)
                if best_key is None or key < best_key:
                    best_key = key
                    best_order = o
                    best_machine = m
                    best_end_time = end_time

        solution[best_machine].append(best_order)
        machine_time[best_machine] = best_end_time
        machine_colour[best_machine] = data['colour'][best_order]
        unassigned_orders.remove(best_order)

    return solution

# relocate + swap 
def improving_search(start, data):

    current = copy_solution(start)
    current_obj = calculate_objective(current, data)

    while True:
        best_neighbor = None
        best_neighbor_obj = current_obj
        neighbours_checked = 0

        for machine_1 in range(len(current)):
            for position_1 in range(len(current[machine_1])):
                for machine_2 in range(len(current)):

                
                    for position_2 in range(number_of_positions(current, machine_1, machine_2)):
                        if machine_1 == machine_2 and position_1 == position_2:
                            continue
                        neighbor = relocate(current, machine_1, position_1, machine_2, position_2)
                        neighbor_obj = calculate_objective(neighbor, data)
                        neighbours_checked += 1
                        if is_better(neighbor_obj, best_neighbor_obj):
                            best_neighbor = neighbor
                            best_neighbor_obj = neighbor_obj

                    
                    for position_2 in range(len(current[machine_2])):
                        if (machine_2, position_2) <= (machine_1, position_1):
                            continue
                        neighbor = swap(current, machine_1, position_1, machine_2, position_2)
                        neighbor_obj = calculate_objective(neighbor, data)
                        neighbours_checked += 1
                        if is_better(neighbor_obj, best_neighbor_obj):
                            best_neighbor = neighbor
                            best_neighbor_obj = neighbor_obj

        if best_neighbor is None:
            print("    Local optimum: 0 better neighbours out of", neighbours_checked, "checked")
            return current

        current = best_neighbor
        current_obj = best_neighbor_obj


data = read_file(FILE_NAME)

start_time = time.time()

# greedy constructive heuristic
greedy_solution = greedy(data)
greedy_obj = calculate_objective(greedy_solution, data)

# improving search until local optimum
final_solution = improving_search(greedy_solution, data)
final_obj = calculate_objective(final_solution, data)

run_time = time.time() - start_time

print("\nGreedy:         penalty =", greedy_obj[0], ", setup =", greedy_obj[1])
print("Final result:   penalty =", final_obj[0], ", setup =", final_obj[1])
print("Time: %.1f s" % run_time)
for m in range(len(final_solution)):
    print(data['machines'][m], final_solution[m])