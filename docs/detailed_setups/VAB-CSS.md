# Setup for VAB-CSS

## Installation
The environment setup for VAB-CSS is mostly straightforward.
In most cases, we do not need any external environments for VAB-CSS, because all it involves is editing local CSS files and taking screenshots for local html files using Python playwright library.

However, there can be one exception that you may need to use a docker image for playwright environment: the default screenshot size (even with a specified viewport size) can be different on some Ubuntu systems.
To check whether you need this step, use [screenshot_docker.py](https://github.com/THUDM/VisualAgentBench/blob/main/src/server/tasks/css_agent/screenshot_docker.py):
```
python screenshot_docker.py path_to_css_dataset/cinema-world/index.html screenshot.png false
```
If you get `1280 1421` from the output (this is the default size that we have tested on multiple Linux/macOS systems), then you are good. This should be the expected behavior. If you get other sizes (which is indeed a rare case), then you will need to take screenshots with the provided docker environment. 

To do this, first pull the docker image:
```
docker pull entslscheia/playwright-screenshot:latest
```

Then you can take screenshot using a command like
```
docker run -it --rm -v [your_local_path_to_screenshot_docker.py]:/app playwright-screenshot:latest python screenshot_docker.py ./cinema-world/index.html screenshot.png false
```
Then replace the `take_screenshot` method in your code with this command (e.g., calling it by using subprocess in Python).

## Get Started
Configure everything within [configs/tasks/css.yaml](https://github.com/THUDM/VisualAgentBench/blob/main/configs/tasks/css.yaml).
