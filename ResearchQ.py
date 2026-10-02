import pandas as pd

def read_file(sample):
    df_orders = pd.read_excel(sample, sheet_name= 'Orders')
    df_machines = pd.read_excel(sample, sheet_name= 'Machines' )
    df_setups = pd.read_excel(sample, sheet_name= 'Setups' )

    data = {}
    data['surface'] = dict(zip(df_orders['Order'],df_orders['Surface']))
    data['colour'] = dict(zip(df_orders['Order'],df_orders['Colour']))
    data['deadline'] = dict(zip(df_orders['Order'],df_orders['Deadline']))
    data['penalty'] = dict(zip(df_orders['Order'],df_orders['Penalty']))

    data['speed'] = dict(zip(df_machines['Machine'], df_machines['Speed']))
    data['machines'] = list(df_machines['Machine'])

    data['setup'] = {}
    for i in range(len(df_setups)):
        colour_from = df_setups.iloc[i, 0]
        colour_to = df_setups.iloc[i,1]
        setup_time = df_setups.iloc[i,2]
        data['setup'][(colour_from,colour_to)] = setup_time

    return data


def greedy_constructive_heuristic(data, rule):
    
    #Builds an initial feasible schedule.
    #rule: 'EDD' (Earliest Due Date) or 'SSA' (Smallest Surface Area)
    
    # 1. Initialize schedule and track the current state of each machine
    schedule = {m: [] for m in data['machines']}
    machine_state = {m: {'time': 0, 'color': None, 'cost': 0} for m in data['machines']}
    
    # Extract the list of orders
    orders_list = list(data['deadline'].keys())
    
    # 2. Sort orders based on the chosen research question rule
    if rule == 'EDD':
        # Sort by Deadline ascending (most urgent first)
        sorted_orders = sorted(orders_list, key=lambda o: data['deadline'][o])
    elif rule == 'SSA':
        # Sort by Surface ascending (smallest area first, acting as our SPT proxy)
        sorted_orders = sorted(orders_list, key=lambda o: data['surface'][o])
    
    
    # 3. Assign orders one by one
    for o in sorted_orders:
        best_machine = None
        best_key = None
        
        # Retrieve order attributes from the unified data structure
        o_surface = data['surface'][o]
        o_color = data['colour'][o]
        o_deadline = data['deadline'][o]
        o_penalty = data['penalty'][o]
        
        # Test the order on every available machine
        for m in data['machines']:
            state = machine_state[m]
            m_speed = data['speed'][m]
            
            # Calculate Setup Time
            setup_time = 0
            if state['color'] is not None and state['color'] != o_color:
                setup_time = data['setup'].get((state['color'], o_color), 0)
                
            # Calculate Finish Time
            start_time = state['time'] + setup_time
            proc_time = o_surface / m_speed
            finish = start_time + proc_time
            
            # Calculate added cost (Penalty for this specific order)
            lateness = max(0, finish - o_deadline)
            added_cost = lateness * o_penalty
            
            # Create the evaluation key (added_cost, finish_time)
            key = (added_cost, finish)
            
            # Determine if this is the best machine so far
            if best_key is None or key < best_key:
                best_key = key
                best_machine = m
                
        # 4. Commit the order to the best machine found
        schedule[best_machine].append(o)
        
        # 5. Update that machine's state for the next iteration
        state = machine_state[best_machine]
        setup_time = 0
        if state['color'] is not None and state['color'] != o_color:
            setup_time = data['setup'].get((state['color'], o_color), 0)
            
        state['time'] = state['time'] + setup_time + (o_surface / data['speed'][best_machine])
        state['color'] = o_color
        state['cost'] += best_key[0]
        
    return schedule

data = read_file("PaintShop - September 2026.xlsx")


# Generate both schedules
edd_schedule = greedy_constructive_heuristic(data, rule='EDD')
ssa_schedule = greedy_constructive_heuristic(data, rule='SSA') # Changed 'SPT' to 'SSA' here

print('Two outcomes are:', edd_schedule, ssa_schedule)


def calculate_objective(schedule, data):
    total_penalty = 0
    
    for m, sequence in schedule.items():
        current_time = 0
        prev_color = None
        speed = data['speed'][m]
        
        for o in sequence:
            curr_color = data['colour'][o]
            
            # 1. Calculate setup time
            setup_time = 0
            if prev_color is not None and prev_color != curr_color:
                setup_time = data['setup'].get((prev_color, curr_color), 0)
                
            # 2. Calculate timing
            start_time = current_time + setup_time
            proc_time = data['surface'][o] / speed
            end_time = start_time + proc_time
            
            # 3. Calculate penalty
            lateness = max(0, end_time - data['deadline'][o])
            cost = lateness * data['penalty'][o]
            total_penalty += cost
            
            # 4. Update trackers for the next order
            current_time = end_time
            prev_color = curr_color
            
    return total_penalty

edd_cost = calculate_objective(edd_schedule, data)
ssa_cost = calculate_objective(ssa_schedule, data)

print('penalty costs:',edd_cost,ssa_cost)
