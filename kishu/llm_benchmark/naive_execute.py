import os

from kishu.jupyterint import KishuForJupyter
from llm_benchmark.ExecAgent import NBGroupExecAgent

data_collect_log_dir = "/home/hanxif2/exp1/kishu/kishu/llm_benchmark/"
group_prefix = "middle"

os.environ[KishuForJupyter.ENV_KISHU_TEST_MODE] = "true"

e2e_times = []
final_run_steps_list = []
num_variables = []
for i in [15]:
    agent = NBGroupExecAgent(f"{group_prefix}_{i}", "non_kishu_start_over", 3)
    log_file_name = f"{group_prefix}_{i}_non_kishu_start_over_log.txt"
    data_collect_log = os.path.join(data_collect_log_dir, f"{group_prefix}_{i}_log.txt")
    with open(log_file_name, 'w') as log_file, open(data_collect_log,'r') as data_collect_log:
        e2e_time, final_run_steps,num_variable = agent.e2e_execute(log_file,data_collect_log)
        print(f"final num_variable:{num_variable}")
        log_file.write(f"e2e time {e2e_time}\n")
        log_file.write(f"final run steps {final_run_steps}\n")
        log_file.write(f"final num variables {num_variable}\n")
        log_file.flush()

        e2e_times.append(e2e_time)
        final_run_steps_list.append(final_run_steps)
        num_variables.append(num_variable)

global_log_file_name = group_prefix + "_global_log.txt"
with open(global_log_file_name, "a") as global_log_file:
    global_log_file.write("Kishu start over group Total time: " + str(sum(e2e_times) / len(e2e_times)) + "\n")
    global_log_file.write("Kishu start over group final run steps: " + str(sum(final_run_steps_list) / len(final_run_steps_list)) + "\n")
    global_log_file.write("Kishu start over group Max variable number: " + str(sum(num_variables) / len(num_variables)) + "\n")






os.environ[KishuForJupyter.ENV_KISHU_TEST_MODE] = "true"

e2e_times = []
final_run_steps_list = []
num_variables = []
for i in [15]:
    agent = NBGroupExecAgent(f"{group_prefix}_{i}", "non_kishu_start_middle", 3)
    log_file_name = f"{group_prefix}_{i}_non_kishu_start_middle_log.txt"
    data_collect_log = os.path.join(data_collect_log_dir, f"{group_prefix}_{i}_log.txt")
    with open(log_file_name, 'w') as log_file, open(data_collect_log, 'r') as data_collect_log:
        e2e_time, final_run_steps, num_variable = agent.e2e_execute(log_file, data_collect_log)
        log_file.write(f"e2e time {e2e_time}\n")
        log_file.write(f"final run steps {final_run_steps}\n")
        log_file.write(f"final num variables {num_variable}\n")
        log_file.flush()

        print(e2e_time)
        print(final_run_steps)
        print(num_variable)

        e2e_times.append(e2e_time)
        final_run_steps_list.append(final_run_steps)
        num_variables.append(num_variable)

global_log_file_name = group_prefix + "_global_log.txt"
with open(global_log_file_name, "a") as global_log_file:
    global_log_file.write("Kishu start middle group Total time: " + str(sum(e2e_times) / len(e2e_times)) + "\n")
    global_log_file.write("Kishu start middle group final run steps: " + str(sum(final_run_steps_list) / len(final_run_steps_list)) + "\n")
    global_log_file.write("Kishu start middle group Max variable number: " + str(sum(num_variables) / len(num_variables)) + "\n")


for i in [15]:
    agent = NBGroupExecAgent(f"{group_prefix}_{i}", "test_semantic_error", 3)
    log_file_name = f"{group_prefix}_{i}_test_semantic_error_log.txt"
    data_collect_log = os.path.join(data_collect_log_dir, f"{group_prefix}_{i}_log.txt")
    with open(log_file_name, 'w') as log_file, open(data_collect_log, 'r') as data_collect_log:
        num_semantic_error_branch = agent.e2e_execute(log_file, data_collect_log)
        log_file.write(f"final num semantic error branch: {num_semantic_error_branch}\n")
        log_file.flush()




# kishu-end-to-end(with code already generated)
# os.environ[KishuForJupyter.ENV_KISHU_TEST_MODE] = "true"

# for i in [15]:
#     agent = NBGroupExecAgent(f"{group_prefix}_{i}", "kishu", 3)
#     log_file_name = f"{group_prefix}_{i}_kishu_log.txt"
#     data_collect_log = os.path.join(data_collect_log_dir, f"{group_prefix}_{i}_log.txt")
#     with open(log_file_name, 'w') as log_file, open(data_collect_log, 'r') as data_collect_log:
#         e2e_time, num_variable = agent.e2e_execute(log_file, data_collect_log)
#         log_file.write(f"e2e time {e2e_time}\n")
#         log_file.write(f"final num variables {num_variable}\n")
#         log_file.flush()
#         print(e2e_time)
#         print(num_variable)