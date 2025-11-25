
<div align="center">
<h1 align="center">
	Beyond Code Pairs: Dialogue-Based Data Generation for LLM Code Translation
</h1>
</div> 

## Introduction  
Beyond traditional source–target code pair datasets, our approach additionally generates (1) verified translations with unit tests for assessing functional consistency, and (2) multi-turn dialogues that capture the reasoning process behind translation refinement. Applied to Fortran→C++ and C++→CUDA, the pipeline yields 11.7k and 3.93k dialogues, respectively. Fine-tuning open-weight LLMs on both code-pair and dialogue data improves translation performance. We further investigate different strategies for fine-tuning data construction and analyze their impact on translation quality, highlighting the effectiveness and flexibility of our generated dialogue data.

## Content 

- `src/` folder contains the source code that is used to run the multi-agent dialogue generation. 
- `data/` folder contains the data that is used to do the model fine-tuning. 
- `sft/` folder contains the configs that is used to fine-tune the models. 
- `analysis/` folder contains the analysis results of the F2C and CPP2Cuda translation tasks. 

