import pandas as pd

def export_to_excel(schedule, data, filename="Final_Schedule.xlsx"):
    
    outputrows = []
    
    for m, sequence in schedule.items():
        current_time = 0
        prev_color = None
        speed = data['speed'][m]
        seq_no = 1 
        
        for o in sequence:
            curr_color = data['colour'][o]
            setup_time = 0

            if prev_color is not None and prev_color != curr_color:
                setup_time = data['setup'].get((prev_color, curr_color), 0)
                
            start_time = current_time + setup_time
            proc_time = data['surface'][o] / speed
            end_time = start_time + proc_time
            tardiness = max(0, end_time - data['deadline'][o])
            penalty_cost = tardiness * data['penalty'][o]
            
            row = {
                'Order': o,
                'Machine': m,
                'SeqNo': seq_no,
                'Setup': setup_time,
                'Start': start_time,
                'Process': proc_time,
                'End': end_time,
                'Deadline': data['deadline'][o],
                'Tardiness': tardiness,
                'Penalty': data['penalty'][o],
                'Cost': penalty_cost
            }
            outputrows.append(row)
            

            current_time = end_time
            prev_color = curr_color
            seq_no += 1  
            
    df_output = pd.DataFrame(outputrows)
    
    df_output.to_excel(filename, sheet_name='Schedule', index=False)