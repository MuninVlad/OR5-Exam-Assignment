import pandas as pd

def read_file(sample):
    df_orders = pd.read_excel(sample, sheet_name= 'Orders')
    df_machines = pd.read_excel('PaintShop - September 2026.xlsx', sheet_name= 'Machines' )
    df_setups = pd.read_excel('PaintShop - September 2026.xlsx', sheet_name= 'Setups' )

print(df_machines)



