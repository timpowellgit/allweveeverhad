#!/bin/bash

python 4_realtime_calibration/web_server.py &
python 4_realtime_calibration/calibration_server.py &
python 2_web/hash_proximity_server.py &

trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

wait
