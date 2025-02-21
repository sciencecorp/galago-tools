## Galago Tools

Every tool runs a gRPC server that exposes a standard interface; Commands are sent to tools for execution.


### Requirements 
```python 
python 3.9.12
```

A lot of legacy lab instruments require to run in python 32 bits and windows. 
You can set a 32 bit environment on mamba or conda. 

### 32 bits python environment.

```
# Set CONDA_FORCE_32BIT environment variable
set CONDA_FORCE_32BIT=1
set CONDA_SUBDIR="win-32"
mamba create -n galago-tools
mamba activate galago-tools
```

### Install 
```
pip install "git+ssh://git@github.com/sciencecorp/galago-tools"
```

### Development 
```
pip install -e .
```


### Generating Wheels. 
This process is still manual. 
```
pip install build
python setup.py bdist_wheel

```
