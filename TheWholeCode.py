import math
import random
import time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches

FILE_NAME = "PaintShop - November 2026.xlsx"   
DATASET_NAME = "November"                       # used in the names of the output files

#  for simulated annealing
MAX_ITERATIONS = 400000         
START_TEMPERATURE = 500         
END_TEMPERATURE = 0.1           
SETUP_WEIGHT = 0.1              
RELOCATE_PROBABILITY = 0.5      
USE_SWAP = True                 
NUMBER_OF_RUNS = 10             
LOG_EVERY = 1000                

EPS = 1e-6       

BAR_COLOURS = {
    'Yellow': '#F2C14E', 'Red': '#E4746A', 'Blue': '#6C9BD2', 'Green': '#6DBE8C',
    'Purple': '#A98BD4', 'Orange': '#F29E5C', 'Black': '#7F7F7F', 'White': '#EDEDED',
}


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


# just few functions to help

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
    # no setup on a clean machine or when the colour stays the same
    if previous_colour is None or previous_colour == colour:
        return 0
    return data['setup'][(previous_colour, colour)]


# objective

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


def sa_value(objective):
    # SA needs one number, penalty + a small weight for setup time
    return objective[0] + SETUP_WEIGHT * objective[1]

# possible moves

def relocate(solution, source_machine, source_position, target_machine, target_position):
    # take one order out and insert it somewhere else
    neighbor = copy_solution(solution)
    order = neighbor[source_machine].pop(source_position)
    neighbor[target_machine].insert(target_position, order)
    return neighbor


def swap(solution, machine_1, position_1, machine_2, position_2):
    # exchange two orders (on the same machine or on two different machines)
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


# Method 1: greedy + improving search

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


# improving search

def improving_search(start, data):
    # best improvement with relocate + swap moves (only relocate if USE_SWAP = False);
    # stops when no neighbour is better -> local optimum
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

                    
                    if not USE_SWAP:
                        continue   
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


# Method 2: random start then SA then improving search

def random_start(data):
    
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


# everything for the output

def build_schedule_table(solution, data):

    rows = []
    for m in range(len(solution)):
        machine_name = data['machines'][m]
        time_now = 0
        previous_colour = None

        for sequence_number in range(len(solution[m])):
            o = solution[m][sequence_number]
            colour = data['colour'][o]

            setup_time = get_setup_time(previous_colour, colour, data)
            start = time_now + setup_time
            process = data['surface'][o] / data['speed'][machine_name]
            end = start + process
            tardiness = max(0, end - data['deadline'][o])

            rows.append({
                'Order': o,
                'Machine': machine_name,
                'SeqNo': sequence_number + 1,
                'Setup': int(setup_time),
                'Start': float(start),
                'Process': float(process),
                'End': float(end),
                'Deadline': int(data['deadline'][o]),
                'Tardiness': float(tardiness),
                'Penalty': int(data['penalty'][o]),
                'Cost': float(tardiness * data['penalty'][o]),
            })

            time_now = end
            previous_colour = colour

    return rows


def export_excel(solution, data, file_name):
    rows = build_schedule_table(solution, data)
    columns = ['Order', 'Machine', 'SeqNo', 'Setup', 'Start', 'Process', 'End',
               'Deadline', 'Tardiness', 'Penalty', 'Cost']
    df = pd.DataFrame(rows, columns=columns)
    df.to_excel(file_name, sheet_name='Schedule', index=False)
    print("  Excel schedule saved:", file_name)


def plot_gantt(solution, data, title, file_name):
    # Gantt chart: one row per machine (M1 at the top); coloured bar = painting,
    # narrow dark band = setup, hatched bar = order finished after its deadline
    rows = build_schedule_table(solution, data)
    fig, ax = plt.subplots(figsize=(16, 1.4 * len(data['machines']) + 2))
 
    for row in rows:
        y = data['machines'].index(row['Machine'])
 
        # setup: narrow dark band just before the order
        if row['Setup'] > 0:
            ax.barh(y, row['Setup'], left=row['Start'] - row['Setup'], height=0.25, color='#4D4D4D')
 
        # painting: colour of the paint, hatched with a dark border if the order is late
        colour = BAR_COLOURS.get(data['colour'][row['Order']], 'lightgrey')
        if row['Tardiness'] > EPS:
            ax.barh(y, row['Process'], left=row['Start'], height=0.7, color=colour,
                    edgecolor='#222222', linewidth=1.8, hatch='///')
        else:
            ax.barh(y, row['Process'], left=row['Start'], height=0.7, color=colour,
                    edgecolor='white', linewidth=1.5)
 
        # label: order name and deadline
        # (small white background so the label is also readable on a hatched bar)
        ax.text(row['Start'] + row['Process'] / 2, y, row['Order'] + "\ndue " + str(row['Deadline']),
                ha='center', va='center', fontsize=7,
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='none', alpha=0.85))
 
    ax.set_yticks(range(len(data['machines'])))
    ax.set_yticklabels(data['machines'])
    ax.invert_yaxis()                      # M1 at the top
    ax.set_xlabel("time")
    ax.grid(True, axis='x', color='#dddddd', linestyle=':')
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    penalty, setup = calculate_objective(solution, data)
    ax.set_title(title + "\ntotal penalty %.2f, total setup time %d" % (penalty, setup))
 
    # legend below the chart (these patches are only used for the legend)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color='#4D4D4D', label='setup'),
                       plt.Rectangle((0, 0), 1, 1, facecolor='white', edgecolor='#222222',
                                     hatch='///', label='late order')],
              loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
 
    plt.tight_layout()
    plt.savefig(file_name)
    plt.close()
    print("  Gantt chart saved:", file_name)


def plot_progress(history, title, file_name):
    iterations = [h[0] for h in history]
    current_values = [h[1] for h in history]
    best_values = [h[2] for h in history]
    temperatures = [h[3] for h in history]

    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True,
                                   gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(iterations, current_values, label="current solution", color="#86b6ef", linewidth=1.5)
    ax1.plot(iterations, best_values, label="best solution", color="#eb6834", linewidth=2)
    ax1.set_ylabel("penalty + " + str(SETUP_WEIGHT) + " * setup (log scale)")
    ax1.set_yscale("log")
    ax1.grid(True, color="#e6e5e0", linewidth=0.8)
    ax1.legend(loc="upper right", frameon=False)
    ax1.set_title(title)

    ax2.plot(iterations, temperatures, color="#52514e", linewidth=1.5)
    ax2.set_ylabel("temperature")
    ax2.set_xlabel("iteration")
    ax2.grid(True, color="#e6e5e0", linewidth=0.8)

    for ax in (ax1, ax2):
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(file_name)
    plt.close()
    print("  SA progress plot saved:", file_name)




data = read_file(FILE_NAME)
print("Dataset:", DATASET_NAME, "|", len(data['orders']), "orders,", len(data['machines']), "machines")

# running method 1
print("\n----- Method 1 -----")
start_time = time.time()

greedy_solution = greedy(data)
greedy_obj = calculate_objective(greedy_solution, data)

final_solution_1 = improving_search(greedy_solution, data)
final_obj_1 = calculate_objective(final_solution_1, data)

time_1 = time.time() - start_time

print("Greedy:                 penalty =", greedy_obj[0], ", setup =", greedy_obj[1])
print("After improving search: penalty =", final_obj_1[0], ", setup =", final_obj_1[1])
print("Time: %.1f s" % time_1)

# running method 2
print("\n----- Method 2 -----")
start_time = time.time()

final_solution_2 = None
final_obj_2 = None
best_history = None
all_results = []

for seed in range(NUMBER_OF_RUNS):
    random.seed(seed)
    sa_solution, history = simulated_annealing(random_start(data), data)
    sa_obj = calculate_objective(sa_solution, data)

    final_solution = improving_search(sa_solution, data)
    final_obj = calculate_objective(final_solution, data)
    all_results.append(final_obj[0])

    print("Seed", seed, "| after SA:", sa_obj, "| after improving search:", final_obj)

    # keep the best run
    if final_obj_2 is None or is_better(final_obj, final_obj_2):
        final_solution_2 = final_solution
        final_obj_2 = final_obj
        best_history = history

time_2 = time.time() - start_time

print("Best result:    penalty =", final_obj_2[0], ", setup =", final_obj_2[1])
print("Average result: penalty = %.2f over %d runs" % (sum(all_results) / len(all_results), NUMBER_OF_RUNS))
print("Time: %.1f s in total, %.1f s per run" % (time_2, time_2 / NUMBER_OF_RUNS))

# the output
print("\n----- Output -----")
plot_gantt(final_solution_1, data, DATASET_NAME + " - Method 1 (greedy + improving search)",
            "gantt_" + DATASET_NAME + "_method1.png")
plot_gantt(final_solution_2, data, DATASET_NAME + " - Method 2 (SA + improving search)",
            "gantt_" + DATASET_NAME + "_method2.png")
plot_progress(best_history, DATASET_NAME + " - simulated annealing progress (best run)",
                "sa_progress_" + DATASET_NAME + ".png")

# the Excel file gets the best schedule of the two methods
if is_better(final_obj_2, final_obj_1):
    print("Best schedule: Method 2")
    export_excel(final_solution_2, data, "Schedule - " + DATASET_NAME + ".xlsx")
else:
    print("Best schedule: Method 1")
    export_excel(final_solution_1, data, "Schedule - " + DATASET_NAME + ".xlsx")