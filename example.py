"""
Paint shop scheduling - one file with everything.

Method 1: greedy constructive heuristic -> discrete improving search -> local optimum
Method 2: metaheuristic (simulated annealing) -> discrete improving search -> local optimum

Run:  python paintshop.py "PaintShop - September 2026.xlsx"

A schedule is a dictionary: machine name -> list of order names (in sequence),
for example {'M1': ['ORD01', 'ORD03'], 'M2': ['ORD02']}.
"""
import math
import random
import sys
import time

import matplotlib.pyplot as plt
from matplotlib.colors import is_color_like
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Reading the data
# ---------------------------------------------------------------------------
def read_data(filename):
    """Read the three sheets and store everything in one dictionary."""
    orders = pd.read_excel(filename, sheet_name='Orders')
    machines = pd.read_excel(filename, sheet_name='Machines')
    setups = pd.read_excel(filename, sheet_name='Setups')

    data = {}
    data['surface'] = dict(zip(orders['Order'], orders['Surface']))
    data['colour'] = dict(zip(orders['Order'], orders['Colour']))
    data['deadline'] = dict(zip(orders['Order'], orders['Deadline']))
    data['penalty'] = dict(zip(orders['Order'], orders['Penalty']))
    data['orders'] = list(orders['Order'])
    data['speed'] = dict(zip(machines['Machine'], machines['Speed']))
    data['machines'] = list(machines['Machine'])

    # setup time between two colours; same colour is not in the table -> 0
    data['setup'] = {}
    for i in range(len(setups)):
        data['setup'][(setups.iloc[i, 0], setups.iloc[i, 1])] = setups.iloc[i, 2]
    return data


# ---------------------------------------------------------------------------
# 2. Evaluating a schedule
# ---------------------------------------------------------------------------
def tardiness(schedule, data):
    """
    Full evaluation. Returns a list of rows (one per order, with all columns of
    the required Excel output) and the total penalty cost.
    """
    rows = []
    total = 0
    for m in schedule:
        c = 0                      # time on this machine (machine is clean at 0)
        previous = None
        for position in range(len(schedule[m])):
            o = schedule[m][position]

            setup = 0
            if previous is not None:
                setup = data['setup'].get((data['colour'][previous], data['colour'][o]), 0)

            start = c + setup
            process = data['surface'][o] / data['speed'][m]
            end = start + process

            late = end - data['deadline'][o]
            if late < 0:
                late = 0
            cost = late * data['penalty'][o]
            total += cost

            rows.append({'Order': o, 'Machine': m, 'SeqNo': position + 1,
                         'Setup': setup, 'Start': start, 'Process': process,
                         'End': end, 'Deadline': data['deadline'][o],
                         'Tardiness': late, 'Penalty': data['penalty'][o],
                         'Cost': cost})
            c = end
            previous = o
    return rows, total


def machine_cost(m, sequence, data):
    """Cost and finish time of ONE machine (fast, no rows). Same logic as tardiness()."""
    c = 0
    cost = 0
    previous = None
    for o in sequence:
        if previous is not None:
            c += data['setup'].get((data['colour'][previous], data['colour'][o]), 0)
        c += data['surface'][o] / data['speed'][m]
        late = c - data['deadline'][o]
        if late > 0:
            cost += late * data['penalty'][o]
        previous = o
    return cost, c


def total_cost(schedule, data):
    """Objective value: total penalty cost of all machines."""
    total = 0
    for m in schedule:
        total += machine_cost(m, schedule[m], data)[0]
    return total


def check_feasible(schedule, data):
    """Every order must appear exactly once, and only on known machines."""
    used = []
    for m in schedule:
        if m not in data['machines']:
            return False
        used += schedule[m]
    return sorted(used) == sorted(data['orders'])


def copy_schedule(schedule):
    return {m: sequence[:] for m, sequence in schedule.items()}


# ---------------------------------------------------------------------------
# 3. Method 1, part A: greedy constructive heuristic
# ---------------------------------------------------------------------------
def greedy(data):
    """
    Take the orders in Earliest-Deadline-First order. Put each order at the end
    of the machine where it adds the least penalty cost (tie: machine where the
    order finishes earliest).
    """
    schedule = {m: [] for m in data['machines']}
    for o in sorted(data['orders'], key=lambda o: data['deadline'][o]):
        best_machine = None
        best_key = None
        for m in data['machines']:
            old_cost = machine_cost(m, schedule[m], data)[0]
            new_cost, finish = machine_cost(m, schedule[m] + [o], data)
            key = (new_cost - old_cost, finish)
            if best_key is None or key < best_key:
                best_key = key
                best_machine = m
        schedule[best_machine].append(o)
    return schedule


# ---------------------------------------------------------------------------
# 4. Neighbourhood: swap two orders, or move one order to another place
# ---------------------------------------------------------------------------
def neighbours(schedule):
    """Generate ALL neighbours of a schedule (used by the improving search)."""
    positions = []                                   # every (machine, index) pair
    for m in schedule:
        for i in range(len(schedule[m])):
            positions.append((m, i))

    # swap: exchange two orders (on the same or on different machines)
    for a in range(len(positions)):
        for b in range(a + 1, len(positions)):
            m1, i = positions[a]
            m2, j = positions[b]
            new = copy_schedule(schedule)
            new[m1][i], new[m2][j] = new[m2][j], new[m1][i]
            yield new

    # relocate: take one order out and insert it anywhere (any machine, any place)
    for (m1, i) in positions:
        for m2 in schedule:
            length = len(schedule[m2]) if m2 != m1 else len(schedule[m2]) - 1
            for p in range(length + 1):
                if m1 == m2 and p == i:
                    continue                          # same place = no move
                new = copy_schedule(schedule)
                order = new[m1].pop(i)
                new[m2].insert(p, order)
                yield new


def random_neighbour(schedule, rng):
    """ONE random neighbour (a random swap or a random relocate), used by SA."""
    new = copy_schedule(schedule)
    positions = [(m, i) for m in new for i in range(len(new[m]))]
    if rng.random() < 0.5:
        (m1, i), (m2, j) = rng.sample(positions, 2)
        new[m1][i], new[m2][j] = new[m2][j], new[m1][i]
    else:
        m1, i = rng.choice(positions)
        order = new[m1].pop(i)
        m2 = rng.choice(list(new))
        p = rng.randint(0, len(new[m2]))
        new[m2].insert(p, order)
    return new


# ---------------------------------------------------------------------------
# 5. Discrete improving search (used by BOTH methods)
# ---------------------------------------------------------------------------
def improving_search(schedule, data):
    """
    Steepest descent: look at all neighbours, move to the best one if it is
    strictly better. Stop when no neighbour is better -> local optimum.
    Returns the schedule, its cost and the cost after every step.
    """
    best_cost = total_cost(schedule, data)
    history = [best_cost]
    improved = True
    while improved:
        improved = False
        best_neighbour = None
        for candidate in neighbours(schedule):
            c = total_cost(candidate, data)
            if c < best_cost - 1e-9:                 # strictly better
                best_neighbour = candidate
                best_cost = c
        if best_neighbour is not None:
            schedule = best_neighbour
            history.append(best_cost)
            improved = True
    return schedule, best_cost, history


# ---------------------------------------------------------------------------
# 6. Method 2, part A: metaheuristic (simulated annealing)
# ---------------------------------------------------------------------------
def random_schedule(data, rng):
    """Random starting schedule: orders in random order on random machines."""
    schedule = {m: [] for m in data['machines']}
    orders = data['orders'][:]
    rng.shuffle(orders)
    for o in orders:
        schedule[rng.choice(data['machines'])].append(o)
    return schedule


def simulated_annealing(data, t_start=100, t_end=0.1, alpha=0.95,
                        moves_per_temp=1000, seed=1):
    """
    Random neighbour each step. Better -> always accept. Worse -> accept with
    probability exp(-increase / T). T is multiplied by alpha after each round.
    This lets the search leave poor local optima early on.
    Returns the best schedule found, its cost, and a history for plotting.
    """
    rng = random.Random(seed)
    current = random_schedule(data, rng)
    current_cost = total_cost(current, data)
    best, best_cost = copy_schedule(current), current_cost
    history = []                                     # (temperature, current, best)

    t = t_start
    while t > t_end:
        for _ in range(moves_per_temp):
            candidate = random_neighbour(current, rng)
            c = total_cost(candidate, data)
            increase = c - current_cost
            if increase < 0 or rng.random() < math.exp(-increase / t):
                current, current_cost = candidate, c
                if current_cost < best_cost:
                    best, best_cost = copy_schedule(current), current_cost
        history.append((t, current_cost, best_cost))
        t = t * alpha
    return best, best_cost, history


# ---------------------------------------------------------------------------
# 7. Output: Excel, Gantt chart, progress plot
# ---------------------------------------------------------------------------
def export_excel(schedule, data, filename):
    """Write the required sheet 'Schedule' (one row per order, Orders-table order)."""
    rows, total = tardiness(schedule, data)
    df = pd.DataFrame(rows)
    index = {o: i for i, o in enumerate(data['orders'])}
    df['_i'] = df['Order'].map(index)
    df = df.sort_values('_i').drop(columns='_i')
    df.to_excel(filename, sheet_name='Schedule', index=False)


def plot_gantt(schedule, data, title, filename):
    """Gantt chart: grey hatched = setup, coloured = painting, red edge = late."""
    rows, total = tardiness(schedule, data)
    fig, ax = plt.subplots(figsize=(13, 3 + len(schedule) * 0.6))
    machines = list(schedule)
    for r in rows:
        y = machines.index(r['Machine'])
        if r['Setup'] > 0:
            ax.barh(y, r['Setup'], left=r['Start'] - r['Setup'], height=0.6,
                    color='lightgrey', hatch='//', edgecolor='black')
        colour = str(data['colour'][r['Order']]).lower()
        if not is_color_like(colour):
            colour = 'tab:orange'
        edge = 'red' if r['Tardiness'] > 0 else 'black'
        ax.barh(y, r['Process'], left=r['Start'], height=0.6, color=colour,
                edgecolor=edge, linewidth=2 if r['Tardiness'] > 0 else 0.8)
        ax.text(r['Start'] + r['Process'] / 2, y, r['Order'][-2:], ha='center',
                va='center', fontsize=7)
    ax.set_yticks(range(len(machines)))
    ax.set_yticklabels(machines)
    ax.invert_yaxis()
    ax.set_xlabel('Time')
    ax.set_title(f'{title}  (total cost = {total:.2f}; red edge = late; grey = setup)')
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)


def plot_progress(history_greedy_dis, history_sa, history_sa_dis, filename):
    """Computational progress of both methods."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    axes[0].plot(history_greedy_dis, marker='o')
    axes[0].set_title('Method 1: improving search after greedy')
    axes[0].set_xlabel('Step')
    axes[0].set_ylabel('Total cost')

    temps = list(range(len(history_sa)))
    axes[1].plot(temps, [h[1] for h in history_sa], label='current', alpha=0.6)
    axes[1].plot(temps, [h[2] for h in history_sa], label='best')
    axes[1].set_title('Method 2: simulated annealing')
    axes[1].set_xlabel('Temperature step')
    axes[1].legend()

    axes[2].plot(history_sa_dis, marker='o')
    axes[2].set_title('Method 2: improving search after SA')
    axes[2].set_xlabel('Step')
    fig.tight_layout()
    fig.savefig(filename, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 8. Main
# ---------------------------------------------------------------------------
def main(filename, seed=1):
    data = read_data(filename)
    print(f"{len(data['orders'])} orders, {len(data['machines'])} machines")

    # Method 1: greedy -> improving search
    t0 = time.time()
    start1 = greedy(data)
    greedy_cost = total_cost(start1, data)
    final1, cost1, hist1 = improving_search(start1, data)
    time1 = time.time() - t0
    print(f'Method 1: greedy = {greedy_cost:.2f} -> local optimum = {cost1:.2f}  ({time1:.1f} s)')

    # Method 2: simulated annealing -> improving search
    t0 = time.time()
    sa_best, sa_cost, hist_sa = simulated_annealing(data, seed=seed)
    final2, cost2, hist2 = improving_search(sa_best, data)
    time2 = time.time() - t0
    print(f'Method 2: SA = {sa_cost:.2f} -> local optimum = {cost2:.2f}  ({time2:.1f} s)')

    # Check and export both schedules
    for name, schedule, cost in [('method1', final1, cost1), ('method2', final2, cost2)]:
        assert check_feasible(schedule, data), name + ' is not feasible'
        export_excel(schedule, data, f'schedule_{name}.xlsx')
        plot_gantt(schedule, data, name, f'gantt_{name}.png')
    plot_progress(hist1, hist_sa, hist2, 'progress.png')

    best = 'method1' if cost1 <= cost2 else 'method2'
    print(f'Best: {best}. Files written: schedule_*.xlsx, gantt_*.png, progress.png')
    return final1, final2


if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else 'PaintShop - September 2026.xlsx'
    main(filename)