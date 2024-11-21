from llm_benchmark.ExecAgent import NBGroupExecAgent

agent = NBGroupExecAgent("middle_1", False, True)
log_file_name = "middle_1_non_kishu_start_over_log.txt"
with open(log_file_name, 'w') as log_file:
    e2e_time, final_run_steps = agent.e2e_execute(log_file)

print(e2e_time)
print(final_run_steps)