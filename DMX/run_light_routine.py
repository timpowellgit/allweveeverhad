# Just runs the routine forever
import light_control as lc
import sys
import time
import os
import serial
import time

SLEEP_BETWEEN_ERR_AND_CYCLE_S = '5'

fastmode=0
if len(sys.argv) >= 2:
  fastmode=int(sys.argv[1])

if fastmode:
  print "running in fastmode"

SERIAL_DIR = '/dev/serial/by-id'
devices = filter(lambda _: 'FT245R' in _, os.listdir(SERIAL_DIR))
assert len(devices) == 1, 'dmx controller not found'
serial_device = os.path.join(SERIAL_DIR, devices[0])

while True:
  try:
    lctr=lc.light_conductor_c(serial_device, fastmode=fastmode)
    while True:
      lctr.full_routine_iteration(verbose=True)
  except Exception as e:
    print 'ERR!',e
    time.sleep(SLEEP_BETWEEN_ERR_AND_CYCLE_S)

  # attempt to close serial port
  try:
    ser = serial.Serial(serial_device)
    ser.close()
  except Exception as e:
    print 'ERR closing port',e
    time.sleep(SLEEP_BETWEEN_ERR_AND_CYCLE_S)

  time.sleep(SLEEP_BETWEEN_ERR_AND_CYCLE_S)
