# TerraMapper

## Overview

A python module to generate an image of a Terraria world from a worldfile, with deepzoom support. This has been rewritten using functions sourced from [flyingsnake](https://github.com/Steffo99/flyingsnake), as I required the image generation to be created within a python stack, and not generated via a shell command. 

## Usage

Either define the following configuration and call the TerraMapper module, providing the configuration as a parameter:

```python
import TerraMapper

# Define the TerraMapper configuration
tmConfig = {
  "draw": {
    "background": True,
    "blocks": True,
    "walls": True,
    "liquids": True,
    "wires": True,
    "paint": True,
    "min_x": 0,
    "min_y": 0,
    "region_width": 0,
    "region_height": 0
  },
  "output": {
    "file_path": ""
  },
  "world": {
    "file_path": ""
  },
  "deep_zoom": {
    "enabled": True
  }
}
# Create a new TerraMapper object
tm = TerraMapper.TerraMapper(config=tmConfig)
```

or create a configuration file and provide the path to TerraMapper

`config.yaml`

```yaml
draw:
  background: true
  blocks: true
  walls: true
  liquids: true
  wires: true
  paint: true
  min_x: 0
  min_y: 0
  region_width: 0
  region_height: 0
output:
  file_path: ""
world:
  file_path: ""
deep_zoom: 
  enabled: true
```

`pythonFile.py`
```python
# Define the TerraMapper configuration file path
configPath = "config.yaml"

# Create a new TerraMapper object
tm = TerraMapper.TerraMapper(configPath=configPath)
```