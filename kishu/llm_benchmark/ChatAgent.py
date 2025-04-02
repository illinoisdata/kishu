import random
random.seed(42)
import re

from openai import OpenAI
import os


class ChatAgent(object):
    def __init__(self, task):
        self.messages = []
        self.next_step = 0  # the step to be executed next, except the prompt, all steps start from 0.
        self.total_steps = 0
        self.next_user_prompt = None
        self.client = OpenAI()
        self.step2message_idx = {}
        self._initialize(task)

    def step(self, last_step_exec_output):
        if last_step_exec_output is None:
            if self.next_user_prompt == None:
                prompt = (f"Please generate the code cell for step {self.next_step + 1}. "
                          f"be careful about error: contains infinity or a value too large for dtype('float32')"
                          f"you should never use plt, sns or other method to draw anything, because we don't have graph system on the computer\n"
                          f"Note: please only generate notebook cell code, no bash or other things.")
            else:
                prompt = self.next_user_prompt
        elif len(last_step_exec_output) < 7000:
            prompt = (f"The output for this code cell is: \n{last_step_exec_output}.\n Please generate the code for next "
                      f"step {self.next_step + 1}")
        else:
            prompt = (f"Please generate the code for next "
            f"step {self.next_step + 1}")
        content = self._generate_gpt_response(prompt)
        self.step2message_idx[self.next_step] = len(self.messages) - 1
        self.next_step += 1
        return content

    def debug(self, output):
        prompt = f"the output of the given code is: {output}, please help me debug it by generating the correct cell code."
        return self._generate_gpt_response(prompt)

    def cal_checkout_prob(self):
        # calculate the probability of checking out at current step
        if self.next_step < 6: # no need to checkout at the first step
            return 0
        if self.next_step == self.total_steps:
            return 1
        return self.next_step / self.total_steps * 0.1

    def cal_target_checkout_step(self):
        # calculate the target step to check out
        if self.next_step == 1:
            return 0
        else:
            return random.randint(min(self.next_step - 2, 5), self.next_step - 2)

    def checkout(self, target_step):
        # checkout the current step
        self.next_step = target_step + 1
        self.next_user_prompt = self.messages[self.step2message_idx[target_step] + 1]["content"]
        self.messages = self.messages[:self.step2message_idx[target_step] + 1]

    def _generate_gpt_response(self, prompt, model="gpt-4o-mini", temperature=0.7):
        client = OpenAI()
        self.messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model=model,
            messages=self.messages,
            temperature=temperature
        )
        content = response.choices[0].message.content
        self.messages.append({'role': 'assistant', 'content': content})
        return content

    def _initialize(self, task):
        prompt = (f"{task}\nIt will be an interactive data science process using notebook. "
                  f"Tell me the steps to do this (without code).\n "
                  f"The steps should include some computation intensive ones such as Hyper-parameter tuning(no more than 3 groups with each group no more than 2 choices), model selection(no more than 2 models to choose from), neural network training(small model only), etc.\n "
                  f"the step should be listed as:\n"
                  f"you should never use plt, sns or other method to draw anything, because we don't have graph system on the computer\n"
                  f"There are XXX steps in total.\n"
                  f"1. XXX\n"
                  f"2. XXX")
        txt_steps = self._generate_gpt_response(prompt)

        # Extract the number of total steps
        return_valid = False
        while not return_valid:
            match = re.search(r"There are (\d+) steps in total\.", txt_steps)
            if match:
                self.total_steps = int(match.group(1))
                return_valid = True
                print(f"Total steps: {self.total_steps}")
            else:
                print("Could not find the total number of steps. Try again.")
                self.messages = []
                txt_steps = self._generate_gpt_response(prompt)


    def modify_step(self, step):
        prompt = (f"now I want to modify step {step + 1}'s code to try a different method but keep the other code the same, "
                  f"i.e., step {step + 1} should still generate the same set of variables for the following steps to use. "
                  f"Help me to generate the code for step {step + 1}.")
        content = self._generate_gpt_response(prompt)
        return content

