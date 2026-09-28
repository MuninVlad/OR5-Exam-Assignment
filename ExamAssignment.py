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

def greedy(data):

    schedule = {}
    for m in data['machines']:
        schedule[m] = []
    for o in sorted(data['orders'], key=lambda o: data['deadline'][o]):
        best_machine = None
        best_key = None
        for m in data['machines']:
            old_cost = machine_cost(.........)
            new_cost, finish = machine_cost(.........)
            key = (new_cost - old_cost, finish)
            if best_key is None or key < best_key:
                best_key = key
                best_machine = m
        schedule[best_machine].append(o)
    return schedule

