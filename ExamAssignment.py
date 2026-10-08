import pandas as pd
import copy

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




def calculate_objective(schedule, data):
    total_penalty = 0
    
    for m, sequence in schedule.items():
        current_time = 0
        prev_color = None
        speed = data['speed'][m]
        
        for o in sequence:
            curr_color = data['colour'][o]
            
            setup_time = 0
            if prev_color is not None and prev_color != curr_color:
                setup_time = data['setup'].get((prev_color, curr_color), 0)
            
            start_time = current_time + setup_time
            proc_time = data['surface'][o] / speed
            end_time = start_time + proc_time
            
            lateness = max(0, end_time - data['deadline'][o])
            cost = lateness * data['penalty'][o]
            total_penalty += cost
            
            current_time = end_time
            prev_color = curr_color
            
    return total_penalty



def greedy(data):
    schedule = {m: [] for m in data['machines']}
    m_time = {m: 0 for m in data['machines']}
    m_color = {m: None for m in data['machines']}
    unassigned_orders = list(data['surface'].keys())
    
    while unassigned_orders:
        best_machine = None
        best_order = None
        best_key = None
        best_end_time = 0
        best_color = None

        for o in unassigned_orders:
            for m in data['machines']:
                prev_color = m_color[m]
                curr_color = data['colour'][o]
                
                setup_time = 0
                if prev_color is not None and prev_color != curr_color:
                    setup_time = data['setup'].get((prev_color, curr_color), 0)
                
                start_time = m_time[m] + setup_time
                proc_time = data['surface'][o] / data['speed'][m]
                end_time = start_time + proc_time
                
                lateness = max(0, end_time - data['deadline'][o])
                added_cost = lateness * data['penalty'][o]
                
                key = (added_cost, end_time)
                
                if best_key is None or key < best_key:
                    best_key = key
                    best_machine = m
                    best_order = o
                    best_end_time = end_time
                    best_color = curr_color
                    
        
        schedule[best_machine].append(best_order)
        m_time[best_machine] = best_end_time
        m_color[best_machine] = best_color
        
        unassigned_orders.remove(best_order)
        
    return schedule




def local_search(schedule, data):
    best_schedule = copy.deepcopy(schedule)
    best_cost = calculate_objective(best_schedule, data)
    
    improved = True
    
    while improved:
        improved = False
        

        for m1 in data['machines']:
            if improved: break
            for i in range(len(best_schedule[m1])):
                if improved: break
                
                for m2 in data['machines']:
                    if improved: break
                    for j in range(len(best_schedule[m2]) + 1): #+1 so we can add at the end
                        
                        if m1 == m2 and i == j:
                            continue #skips the rest of the loop
                            
                        candidate = copy.deepcopy(best_schedule)
                        order = candidate[m1].pop(i)
                        candidate[m2].insert(j, order)
                        
                        candidate_cost = calculate_objective(candidate, data)
                        
                        if candidate_cost < best_cost:
                            best_schedule = candidate
                            best_cost = candidate_cost
                            improved = True
                            break 

    return best_schedule




file = 'PaintShop - September 2026.xlsx'
data = read_file(file)

greedy_schedule = greedy(data)
greedy_cost = calculate_objective(greedy_schedule, data)
print(f"Greedy Cost: {greedy_cost}")


ls_schedule = local_search(greedy_schedule, data)
ls_cost = calculate_objective(ls_schedule, data)
print(f"Local Search Cost: {ls_cost}")
