# SFT models using Llama Factory 

These models are trained using single H200. 

## Setup Environment 
```
conda create -n f2cpp_train python=3.11 -y 
conda activate f2cpp_train

git clone https://github.com/hiyouga/LLaMA-Factory.git
cd LLaMA-Factory
pip install -e ".[torch,metrics,deepspeed]" --no-build-isolation
```

## Train models

Logining into wandb to keep track of the training process
```
wandb login
```

```bash
FORCE_TORCHRUN=1 llamafactory-cli train ./configs/<configuration_file> 
```

You can see example in `configs`.


