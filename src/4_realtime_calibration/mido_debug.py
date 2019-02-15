import mido

inport = mido.open_input('New Port', virtual =True)

for msg in inport.iter_pending():
	print msg
# inport = mido.open_input('New Port', virtual =True)

# while True:
#   for msg in inport.iter_pending():
#     print msg
