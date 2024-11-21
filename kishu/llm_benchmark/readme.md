# To colloct data and run Kishu group
1. copy the task you want to collect data from 'prompts.json' to 'prompts_all.json'
2. in kishu dir, run
```bash
OPENAI_API_KEY=sk-8mgzIwOCe_1BuNA9NGFsucS2h929ZiWIfDy8qqM-enT3BlbkFJUIxVWneWOM2YjkMGTCaJovRvUDQC-iNvlW27HaNo0A python llm_benchmark/data_gen.py
```
3. You can see the generated result and the data `<task_name>_*.ipynb` and `<task_name>_log.txt`


# To run notebooks with non-kishu and startover for everynotebook
1. Change the task name in `naive_execute.py` to the task you want to run
2. Run
```bash
python naive_execute.py
```
3. You can see result in <task_name>_non_kishu_start_over_log.txt