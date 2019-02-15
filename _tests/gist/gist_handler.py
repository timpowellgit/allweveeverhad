import sys
from PIL import Image
import random
import os
import tempfile
import subprocess

BIN = '/Users/greg/Downloads/lear_gist-1.1/compute_gist'

file_path = sys.argv[1]


im = Image.open(file_path)
out_path = os.path.join(tempfile.mkdtemp(), 'file.ppm')
im.save(out_path)

popen = subprocess.Popen([BIN, out_path], stdout=subprocess.PIPE)
popen.wait()
output = popen.stdout.read()

output = map(float, output.strip().split())

print('output', output)
