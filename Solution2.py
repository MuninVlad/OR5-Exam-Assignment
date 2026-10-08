# use relocate for the Discrete Improving Search
# use SA for metaheuristic 

import math
import random
import pandas as pd




def read_file(sample):
    df_orders = pd.read_excel(sample, sheet_name='Orders')
    df_machines = pd.read_excel(sample, sheet_name='Machines')
    df_setups = pd.read_excel(sample, sheet_name='Setups')

    data = {}
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


data = read_file("PaintShop - November 2026.xlsx")
orders = list(data['surface'].keys())


SETUP_WEIGHT = 0.1   # weight of setup time inside SA
EPS = 1e-6           # tolerance for comparing decimal numbers



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



def evaluate_machine(machine_orders, m):
    time = 0
    total_penalty = 0
    total_setup = 0
    previous_colour = None

    for o in machine_orders:
        colour = data['colour'][o]

       
        if previous_colour is not None and previous_colour != colour:
            setup_time = data['setup'][(previous_colour, colour)]
            time = time + setup_time
            total_setup = total_setup + setup_time

        
        machine_name = data['machines'][m]
        time = time + data['surface'][o] / data['speed'][machine_name]

        
        lateness = max(0, time - data['deadline'][o])
        total_penalty = total_penalty + data['penalty'][o] * lateness

        previous_colour = colour

    return total_penalty, total_setup


def calculate_objective(solution):
    total_penalty = 0
    total_setup = 0
    for m in range(len(solution)):
        machine_penalty, machine_setup = evaluate_machine(solution[m], m)
        total_penalty = total_penalty + machine_penalty
        total_setup = total_setup + machine_setup
    total_penalty = round(float(total_penalty), 6)
    total_setup = round(float(total_setup), 6)
    return total_penalty, total_setup


def is_better(new, old):
    
    if new[0] < old[0] - EPS:
        return True
    if abs(new[0] - old[0]) <= EPS and new[1] < old[1] - EPS:
        return True
    return False



def random_start():
    
    solution = []
    for machine in data['machines']:
        solution.append([])

    
    remaining = list(orders)
    random.shuffle(remaining)
    for o in remaining:
        m = random.randrange(len(data['machines']))
        solution[m].append(o)
    return solution



def relocate(solution, source_machine, source_position, target_machine, target_position):
    
    neighbor = copy_solution(solution)
    order = neighbor[source_machine].pop(source_position)
    neighbor[target_machine].insert(target_position, order)
    return neighbor


def simulated_annealing(start, initial_temperature=100, max_iterations=1000000,
                        iterations_per_temperature=1000, alpha=0.9938):
    current = copy_solution(start)
    current_obj = calculate_objective(current)

    
    costs = []
    for m in range(len(current)):
        costs.append(evaluate_machine(current[m], m))

    best = copy_solution(current)
    best_obj = current_obj
    temperature = initial_temperature

    for iteration in range(max_iterations):

        
        while True:
            source_machine = random.randrange(len(current))
            if len(current[source_machine]) == 0:
                continue
            source_position = random.randrange(len(current[source_machine]))
            target_machine = random.randrange(len(current))
            target_position = random.randrange(number_of_positions(current, source_machine, target_machine))

            # skip moves that change nothing
            if target_machine == source_machine and target_position == source_position:
                continue
            break

        neighbor = relocate(current, source_machine, source_position, target_machine, target_position)

        
        new_source_cost = evaluate_machine(neighbor[source_machine], source_machine)
        if target_machine == source_machine:
            new_target_cost = new_source_cost
        else:
            new_target_cost = evaluate_machine(neighbor[target_machine], target_machine)

        new_penalty = current_obj[0] - costs[source_machine][0] + new_source_cost[0]
        new_setup = current_obj[1] - costs[source_machine][1] + new_source_cost[1]
        if target_machine != source_machine:
            new_penalty = new_penalty + new_target_cost[0] - costs[target_machine][0]
            new_setup = new_setup + new_target_cost[1] - costs[target_machine][1]
        new_obj = (round(new_penalty, 6), round(new_setup, 6))

        
        current_value = current_obj[0] + SETUP_WEIGHT * current_obj[1]
        new_value = new_obj[0] + SETUP_WEIGHT * new_obj[1]
        delta = current_value - new_value

        
        if delta >= 0 or random.random() < math.exp(delta / temperature):
            current = neighbor
            costs[source_machine] = new_source_cost
            costs[target_machine] = new_target_cost
            current_obj = new_obj

            
            if current_obj < best_obj:
                best = copy_solution(current)
                best_obj = current_obj

        
        if (iteration + 1) % iterations_per_temperature == 0:
            temperature = temperature * alpha

    return best



def improving_search(start):
    current = copy_solution(start)
    current_obj = calculate_objective(current)

    while True:
        best_neighbor = None
        best_neighbor_obj = current_obj

        
        for source_machine in range(len(current)):
            for source_position in range(len(current[source_machine])):
                for target_machine in range(len(current)):
                    for target_position in range(number_of_positions(current, source_machine, target_machine)):

                        
                        if target_machine == source_machine and target_position == source_position:
                            continue

                        neighbor = relocate(current, source_machine, source_position,
                                            target_machine, target_position)
                        neighbor_obj = calculate_objective(neighbor)

                        if is_better(neighbor_obj, best_neighbor_obj):
                            best_neighbor = neighbor
                            best_neighbor_obj = neighbor_obj

       
        if best_neighbor is None:
            return current

        current = best_neighbor
        current_obj = best_neighbor_obj



start = random_start()
sa_solution = simulated_annealing(start)
final_solution = improving_search(sa_solution)

print("Start:", calculate_objective(start))
print("SA:", calculate_objective(sa_solution))
print("After improving search:", calculate_objective(final_solution), "(penalty cost, setup time)")
for m in range(len(final_solution)):
    print(data['machines'][m], final_solution[m])