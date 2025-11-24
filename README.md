
<div align="center">
<h1 align="center">
	Beyond Code Pairs: Dialogue-Based Data Generation for LLM Code Translation
</h1>
</div> 

## Introduction  
Beyond traditional source–target code pair datasets, our approach additionally generates (1) verified translations with unit tests for assessing functional consistency, and (2) multi-turn dialogues that capture the reasoning process behind translation refinement. Applied to Fortran→C++ and C++→CUDA, the pipeline yields 11.7k and 3.93k dialogues, respectively. Fine-tuning open-weight LLMs on both code-pair and dialogue data improves translation performance. We further investigate different strategies for fine-tuning data construction and analyze their impact on translation quality, highlighting the effectiveness and flexibility of our generated dialogue data.

## Content 

- `agent.py` is the file that contains the agent workflow that is implemented based on our designed agentic workflow. 
- `data/` folder contains the data that is used to train the agent. 
- `sft/` folder contains the configs that is used to train the SFT models. 
- `prompt_f2c_output_comparison.py` is the file that contains the prompts that is used to generate the code pairs. 


