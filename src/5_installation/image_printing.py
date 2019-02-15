import time
from subprocess import call
import os
import sys

DEBUG = os.environ['INSTALLATION_PRINT_DEBUG'] == 'true'
DEBUG_FAKE_PRINTING_DELAY_S = 5

def print_file(file_name):
  print 'PRINTING {}'.format(file_name)

  if DEBUG:
    print 'DEBUG DEBUG DEBUG not actually printing...'
    time.sleep(DEBUG_FAKE_PRINTING_DELAY_S)
    return

  # actually print!
  call(["lp", file_name])

  # done..???

if __name__ == '__main__':
  print_file(sys.argv[1])
