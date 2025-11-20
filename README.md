
<div align="center">
<h1 align="center">
	Beyond Code Pairs: Dialogue-Based Data Generation for LLM Code Translation
</h1>
</div> 

## Introduction  
Beyond traditional source–target code pair datasets, our approach additionally generates (1) verified translations with unit tests for assessing functional consistency, and (2) multi-turn dialogues that capture the reasoning process behind translation refinement. Applied to Fortran→C++ and C++→CUDA, the pipeline yields 11.7k and 3.93k dialogues, respectively. Fine-tuning open-weight LLMs on both code-pair and dialogue data improves translation performance. We further investigate different strategies for fine-tuning data construction and analyze their impact on translation quality, highlighting the effectiveness and flexibility of our generated dialogue data.

## Quickstart 

```
conda create -n f2cpp_train python=3.11 -y 
conda activate f2cpp_train
pip install -r requirements.txt
```



