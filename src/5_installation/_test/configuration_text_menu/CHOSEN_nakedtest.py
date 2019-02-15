# importing readline fixes arrow movement when calling raw_input!
import readline
import os
import time
import re

threshold = 0.9
stop_printing = False

def printsleep(s):
  print s
  time.sleep(3)

while True:
  os.system('clear')
  print("""
  * All we'd ever need is one another *

  1. set print threshold [currently: {threshold}]
  1. set web threshold [currently: {threshold}]
  2. {stop_printing}
  3. force 1 print
  4. exit
  """.format(
    threshold=threshold,
    stop_printing='{} printing'.format('start' if stop_printing else 'stop')))
  ans = raw_input("What would you like to do? ")
  if ans=="1":
    value = raw_input('new threshold? ')
    res = re.match('^([\d]+)\.([\d]+)$', value)
    if not res:
      printsleep('invalid format -- must be given as #.## i.e. 3.45 or 0.2')
      continue
    threshold = float('{}.{}'.format(*res.groups()))
  elif ans == '2':
    stop_printing = not stop_printing
  elif ans=="4":
    break
  else:
    printsleep("\n Not Valid Choice Try again")
