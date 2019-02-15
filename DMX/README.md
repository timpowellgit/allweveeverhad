Requires DmxPy in PYTHONPATH, e.g., do

PYTHONPATH="./DmxPy:${PYTHONPATH}" ...

before running in this directory so Python knows where the module is.

For a simple test, run (on OSX, Unix)

    PYTHONPATH="./DmxPy:${PYTHONPATH}" python light_routine_test.py

The above commands must be run from the directory containing this README file.

# How to run on Windows

Open command-prompt as ***administrator*** (right-click on Command Prompt and select run as administrator)

navigate to adam-dmx-controller

To run the installation, run:

run_light_routine.bat

To run a test, run:

run_light_routine_fastmode.bat

# To adjust the parameters look in light_control.py

