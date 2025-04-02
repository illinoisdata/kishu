import os
import json
from random import random
import nbformat

from kishu.jupyterint import KishuForJupyter
from llm_benchmark.ChatAgent import ChatAgent
from llm_benchmark.ExecAgent import KishuExecAgent
from llm_benchmark.utils import check_file_exist, get_cell_code, append_cell, copy_cell

os.environ[KishuForJupyter.ENV_KISHU_TEST_MODE] = "true"

# tmpg6pp_uvs.ipynb

nb_dir = "./notebooks/"  # dir for generated notebooks
if not os.path.exists(nb_dir):
    os.makedirs(nb_dir)

# Load the JSON file
with open('prompts.json', 'r') as file:
    configurations = json.load(file)

    # Iterate through the list of configurations
    for config in configurations:
        data = config['data']
        task = config['task']
        kishu_e2e_times = []
        kishu_longest_lengths = []
        kishu_max_var_nums = []
        # check if all files in data exist
        if not check_file_exist(data):
            print("Alarm: data doesn't exist for ", config['exp_name'])
            continue
        for i in range(20,23):
            exp_name = config['exp_name'] + "_" + str(i)
            kishu_e2e_time = 0
            kishu_longest_length = 0
            kishu_current_length = 0
            max_var_num = 0
            print("start collecting code111 branches for experiment: ", exp_name)
            log_file_name = exp_name + "_" + "log.txt"  # log file record the data gen process, it can be used to recover the commit graph
            with open(log_file_name, 'w') as log_file:
                chat_agent = ChatAgent(task)
                exec_agent = KishuExecAgent()
                log_file.write(str(exec_agent.tmp_nb_path) + "\n")

                path_num = 0

                nb = nbformat.v4.new_notebook()

                output = None  # execution output of the previous step
                while path_num < 3:
                    cell_code = get_cell_code(chat_agent.step(output))  # feed the output of last step
                    print(f"executing:{cell_code}")
                    output, traceback, exec_time = exec_agent.execute(cell_code, chat_agent.next_step - 1)
                    print("execution output", output)
                    if traceback is not "" and traceback != None:
                        print("trace back", traceback)
                    rollback_prob = 0

                    # try to generate non-error result
                    retry = 1
                    while traceback is not "" and traceback is not None and retry > 0:
                        print(traceback)
                        retry -= 1
                        cell_code = get_cell_code(chat_agent.debug(traceback))
                        print(f"executing:{cell_code}")
                        output, traceback, exec_time = exec_agent.execute(cell_code, chat_agent.next_step - 1)

                    # if still has error,
                    if traceback is not "" and traceback is not None:
                        chat_agent.next_step -= 1  # give up this step directly
                        print("give up this path because error not solved")
                        log_file.write(f"give up this path because error not solved")
                        log_file.flush()
                        rollback_prob = 1
                    else:
                        # write the log, and cell to notebook file
                        kishu_e2e_time += exec_time
                        log_file.write(f"exec step {chat_agent.next_step - 1}. Time: {exec_time}\n")
                        print(f"exec step {chat_agent.next_step - 1}. Time: {exec_time}")
                        log_file.flush()

                        append_cell(nb, cell_code)
                        kishu_current_length += 1
                        rollback_prob = chat_agent.cal_checkout_prob()


                    # randomly rollback
                    if random() < rollback_prob:
                        # flush the current path as a notebook
                        with open(f"{nb_dir + exp_name}_{path_num}.ipynb", "w") as f:
                            nbformat.write(nb, f)

                        path_num += 1
                        kishu_longest_length = max(kishu_current_length, kishu_longest_length)
                        if max_var_num > exec_agent.num_variables():
                            print(max_var_num)
                            print(exec_agent.shell.user_ns.keys())
                        max_var_num = max(max_var_num, exec_agent.num_variables())

                        if path_num >= 3:
                            break

                        # checkout agents to target step
                        target_step = chat_agent.cal_target_checkout_step()
                        # debug: verify the messages
                        # print("messages:\n", chat_agent.messages)
                        checkout_time = exec_agent.checkout(target_step)
                        chat_agent.checkout(target_step)

                        # write log about the checkout
                        kishu_e2e_time += checkout_time
                        log_file.write(f"checkout to step {target_step}. Time: {checkout_time}\n")
                        print(f"checkout to step {target_step}. Time: {checkout_time}")
                        log_file.flush()

                        # update nb for new path
                        new_nb = nbformat.v4.new_notebook()
                        copy_cell(new_nb, nb, target_step)
                        kishu_current_length = target_step + 1
                        nb = new_nb

                        # clear the output for previous step
                        output = None

                log_file.write(f"Experiment: {exp_name} finished\n")
                print("Experiment: ", exp_name, "finished")
                log_file.write("Kishu group Total time: " + str(kishu_e2e_time) + "\n")
                print("Kishu group Total time: ", kishu_e2e_time)
                log_file.write("Kishu group Longest path length: " + str(kishu_longest_length) + "\n")
                print("Kishu group Longest path length: ", kishu_longest_length)
                log_file.write("Kishu group Max variable number: " + str(max_var_num) + "\n")
                print("Kishu group Max variable number: ", max_var_num)
                kishu_e2e_times.append(kishu_e2e_time)
                kishu_longest_lengths.append(kishu_longest_length)
                kishu_max_var_nums.append(max_var_num)

        global_log_file_name = config['exp_name'] + "_global_log.txt"
        with open(global_log_file_name, "w") as global_log_file:
            global_log_file.write("Kishu group Total time: " + str(sum(kishu_e2e_times) / len(kishu_e2e_times)) + "\n")
            global_log_file.write("Kishu group Longest path length: " + str(sum(kishu_longest_lengths) / len(kishu_longest_lengths)) + "\n")
            global_log_file.write("Kishu group Max variable number: " + str(sum(kishu_max_var_nums) / len(kishu_max_var_nums)) + "\n")

