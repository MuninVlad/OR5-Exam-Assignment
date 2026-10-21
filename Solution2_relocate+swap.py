

import math
import random
import time
import pandas as pd
import matplotlib.pyplot as plt


FILE_NAME = "PaintShop - November 2026.xlsx"   

# simulated annealing
MAX_ITERATIONS = 200000        
START_TEMPERATURE = 2000        
END_TEMPERATURE = 0.1           
SETUP_WEIGHT = 0.1              
RELOCATE_PROBABILITY = 0.5     
NUMBER_OF_RUNS = 10             
LOG_EVERY = 1000               

EPS = 1e-6                      # tolerance for comparing decimal numbers


# read data

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

    
    colours = set(data['colour'].values())
    for colour_from in colours:
        for colour_to in colours:
            if colour_from != colour_to and (colour_from, colour_to) not in data['setup']:
                raise ValueError("Missing setup time from " + colour_from + " to " + colour_to)

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


# the objective

def evaluate_machine(machine_orders, m, data):

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
    # lower penalty is better; if the penalty is equal, lower setup is better
    if new[0] < old[0] - EPS:
        return True
    if abs(new[0] - old[0]) <= EPS and new[1] < old[1] - EPS:
        return True
    return False


def sa_value(objective):
    # SA needs one number: penalty + a small weight for setup time
    return objective[0] + SETUP_WEIGHT * objective[1]



def relocate(solution, source_machine, source_position, target_machine, target_position):
    # take one order out and insert it somewhere else
    neighbor = copy_solution(solution)
    order = neighbor[source_machine].pop(source_position)
    neighbor[target_machine].insert(target_position, order)
    return neighbor


def swap(solution, machine_1, position_1, machine_2, position_2):
    # exchange two orders 
    neighbor = copy_solution(solution)
    order_1 = neighbor[machine_1][position_1]
    order_2 = neighbor[machine_2][position_2]
    neighbor[machine_1][position_1] = order_2
    neighbor[machine_2][position_2] = order_1
    return neighbor


def random_move(solution):
    # makes one random relocate or swap move
    while True:
        machine_1 = random.randrange(len(solution))
        machine_2 = random.randrange(len(solution))
        if len(solution[machine_1]) == 0:
            continue

        position_1 = random.randrange(len(solution[machine_1]))

        if random.random() < RELOCATE_PROBABILITY:
            position_2 = random.randrange(number_of_positions(solution, machine_1, machine_2))
            if machine_1 == machine_2 and position_1 == position_2:
                continue  
            return relocate(solution, machine_1, position_1, machine_2, position_2)
        else:
            if len(solution[machine_2]) == 0:
                continue
            position_2 = random.randrange(len(solution[machine_2]))
            if machine_1 == machine_2 and position_1 == position_2:
                continue  
            return swap(solution, machine_1, position_1, machine_2, position_2)


# improving search

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

                    # all relocate moves
                    for position_2 in range(number_of_positions(current, machine_1, machine_2)):
                        if machine_1 == machine_2 and position_1 == position_2:
                            continue
                        neighbor = relocate(current, machine_1, position_1, machine_2, position_2)
                        neighbor_obj = calculate_objective(neighbor, data)
                        neighbours_checked += 1
                        if is_better(neighbor_obj, best_neighbor_obj):
                            best_neighbor = neighbor
                            best_neighbor_obj = neighbor_obj

                    # all swap moves
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


# SA

def random_start(data):
    # every order on a random machine, in random order
    solution = []
    for m in range(len(data['machines'])):
        solution.append([])

    remaining = list(data['orders'])
    random.shuffle(remaining)
    for o in remaining:
        m = random.randrange(len(data['machines']))
        solution[m].append(o)
    return solution


def simulated_annealing(start, data):
    current = copy_solution(start)
    current_obj = calculate_objective(current, data)

    best = copy_solution(current)
    best_obj = current_obj

    temperature = START_TEMPERATURE
    alpha = (END_TEMPERATURE / START_TEMPERATURE) ** (1 / MAX_ITERATIONS)

    history = []   

    for iteration in range(MAX_ITERATIONS):
        neighbor = random_move(current)
        neighbor_obj = calculate_objective(neighbor, data)

        delta = sa_value(neighbor_obj) - sa_value(current_obj)  

       
        if delta <= 0 or random.random() < math.exp(-delta / temperature):
            current = neighbor
            current_obj = neighbor_obj

            if is_better(current_obj, best_obj):
                best = copy_solution(current)
                best_obj = current_obj

        temperature = temperature * alpha

        if iteration % LOG_EVERY == 0:
            history.append((iteration, sa_value(current_obj), sa_value(best_obj), temperature))

    return best, history

def run_method_2(data):
    best_solution = None
    best_obj = None
    best_history = None
    results = []   

    for seed in range(NUMBER_OF_RUNS):
        random.seed(seed)
        start_time = time.time()
        sa_solution, history = simulated_annealing(random_start(data), data)
        sa_obj = calculate_objective(sa_solution, data)
        final_solution = improving_search(sa_solution, data)
        final_obj = calculate_objective(final_solution, data)
        run_time = time.time() - start_time

        print("  Method 2 | seed", seed, "| after SA:", sa_obj, "| after improving search:", final_obj,
              "| time: %.1f s" % run_time)
        results.append((seed, sa_obj, final_obj, run_time))

        if best_obj is None or is_better(final_obj, best_obj):
            best_solution = final_solution
            best_obj = final_obj
            best_history = history

    return best_solution, best_obj, best_history, results



def plot_progress(history, title, file_name):
    iterations = [h[0] for h in history]
    current_values = [h[1] for h in history]
    best_values = [h[2] for h in history]
    temperatures = [h[3] for h in history]

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(iterations, current_values, label="current solution", alpha=0.6)
    ax1.plot(iterations, best_values, label="best solution", linewidth=2)
    ax1.set_xlabel("iteration")
    ax1.set_ylabel("penalty + " + str(SETUP_WEIGHT) + " * setup")
    ax1.set_yscale("log")

    ax2 = ax1.twinx()   
    ax2.plot(iterations, temperatures, color="grey", linestyle="--", label="temperature")
    ax2.set_ylabel("temperature")

    fig.legend(loc="upper center", bbox_to_anchor=(0.5, 0.92))
    plt.title(title)
    plt.tight_layout()
    plt.savefig(file_name)
    plt.close()
    print("  SA progress plot saved:", file_name)


data = read_file(FILE_NAME)
best_solution, best_obj, best_history, results = run_method_2(data)

average = sum(r[2][0] for r in results) / len(results)
print("\nBest result:    penalty =", best_obj[0], ", setup =", best_obj[1])
print("Average result: penalty = %.2f over %d runs" % (average, len(results)))
for m in range(len(best_solution)):
    print(data['machines'][m], best_solution[m])

plot_progress(best_history, "Simulated annealing progress (best run)", "sa_progress.png")