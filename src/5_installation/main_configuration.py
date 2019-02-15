import readline # importing readline fixes arrow movement when calling raw_input!
import os
import time
import re
from configuration_values import \
                          get_web_twitter_threshold, set_web_twitter_threshold, \
                          get_print_threshold, set_print_threshold, \
                          set_force_print_flag, \
                          get_stop_printing_flag, set_stop_printing_flag, \
                          get_print_every_once_in_n_matches, \
                          set_print_every_once_in_n_matches, \
                          get_web_twitter_every_once_in_n_matches, \
                          set_web_twitter_every_once_in_n_matches, \
                          get_force_print_threshold, set_force_print_threshold
from models import db

ARTWORKS_SQLITE_PATH = os.environ['ARTWORKS_SQLITE_PATH']

db.init(ARTWORKS_SQLITE_PATH)

def input_float(prompt):
  value = raw_input('{}? '.format(prompt))
  res = re.match(r'^([\d]+)\.([\d]+)$', value)
  if not res:
    printsleep('ERR Invalid format! Threshold must be given as #.## i.e. 3.45 or 0.2')
    return None
  return float('{}.{}'.format(*res.groups()))

def input_int(prompt):
  value = raw_input('{}? '.format(prompt))
  res = re.match(r'^([\d]+)$', value)
  if not res:
    printsleep('ERR Invalid format! Value must be given as ## i.e. 1 or 12')
    return None
  return int(res.groups()[0])

def printsleep(s):
  print '\n {}'.format(s)
  time.sleep(2)

while True:
  os.system('clear')
  print("""
  * All we'd ever need is one another *

  WEB & TWITTER
  1. set web & twitter threshold [currently: {web_twitter_threshold}]
  2. post to web & twitter once every [currently: {once_every_n_web_twitter}] matches

  PRINT
  3. printing is {printing_enabled} (select option to switch)
  4. set print threshold [currently: {print_threshold}]
  5. print once every [currently: {once_every_n_print}] matches

  FORCE PRINT
  6. set print force threshold [currently: {force_print_threshold}]
  7. force 1 print
  """.format(
    web_twitter_threshold=get_web_twitter_threshold(),
    once_every_n_web_twitter=get_web_twitter_every_once_in_n_matches(),

    print_threshold=get_print_threshold(),
    once_every_n_print=get_print_every_once_in_n_matches(),

    printing_enabled=['ENABLED', 'DISABLED'][
                        bool(get_stop_printing_flag())],
    force_print_threshold=get_force_print_threshold(),
  ))
  ans = raw_input("Please input menu number> ")

  # web & twitter
  if ans == '1':
    value = input_float('new web & twitter threshold'.format())
    if value is None:
      continue
    set_web_twitter_threshold(value)
  elif ans == '2':
    value = input_int('new "post to web & twitter once every N matches" value')
    if value is None:
      continue
    set_web_twitter_every_once_in_n_matches(value)
  # print
  elif ans == '3':
    set_stop_printing_flag(not get_stop_printing_flag())
  elif ans == '4':
    value = input_float('new print threshold'.format())
    if value is None:
      continue
    set_print_threshold(value)
  elif ans == '5':
    value = input_int('new "once every N print" value')
    if value is None:
      continue
    set_print_every_once_in_n_matches(value)
  # force print
  elif ans == '6':
    value = input_float('new force print threshold'.format())
    if value is None:
      continue
    set_force_print_threshold(value)
  elif ans == '7':
    set_force_print_flag(True)
    printsleep('OK! Forcing print, expect one soon. More info will be printed in the main program output.')
  else:
    printsleep('Not a valid choice. Try again')
