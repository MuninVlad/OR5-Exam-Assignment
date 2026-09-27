import pandas as pd 

df = pd.read_excel("Challenge 1 - medium sized instance.xlsx")
df = df.sort_values('DueDate').reset_index()

def tardiness(sample):
    sample = sample.copy()
    completion_time = []
    c = 0 
    for i in range(len(sample)):
        c += sample.loc[i,'ProcessingTime']
        completion_time.append(c)
    sample['CompletionTime'] = completion_time

    t = []
    for i in range(len(sample)):
        late = sample.loc[i,'CompletionTime'] - sample.loc[i,'DueDate']
        if late < 0:
            late = 0
        t.append(late)
    sample['Tardiness'] = t

    total = sum(sample['Tardiness'])

    return sample,total

def swap_rows(sample):
    sample,best_total = tardiness(sample)
    improved = True

    while improved:
        improved = False
        best_candidate = sample
        best_candidate_total = best_total
        n = len(sample)
        for i in range(n):
            for j in range(i+1,n):
                candidate = sample.copy()
                candidate.iloc[[i,j]] = candidate.iloc[[j,i]].values
                candidate, candidate_total = tardiness(candidate)

                if candidate_total < best_candidate_total:
                    best_candidate = candidate
                    best_candidate_total = candidate_total
        if best_candidate_total < best_total:
            sample = best_candidate
            best_total = best_candidate_total
            improved = True
    return sample,best_total
edd_schedule, edd_total = tardiness(df)
print(f'The edd sequence is \n{edd_schedule}')
print(f'edd_total = {edd_total}')

final_schedule, final_total = swap_rows(df)
print(f'Final schedule is \n{final_schedule}')
print(f'Final_total is {final_total}')