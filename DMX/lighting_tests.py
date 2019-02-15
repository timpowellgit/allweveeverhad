import time
import light_control

lc = light_control.light_ctl_c('/dev/ttyUSB0')

test_send_val = False
test_ramp = False
test_pulse = True

if test_send_val:
    print "testing send_val"
    val = 100
    for i in range(6):
        lc.send_val(1,val)
        val = 100 - val
        time.sleep(1)

if test_ramp:
    print "testing ramp"
    vals=[100,50,80,0]
    durs=[1,0.5,0.1,2]
    res=0.1
    for val,dur in zip(vals,durs):
        lc.ramp(1,val,dur,res)

if test_pulse:
    print "testing pulse"
    vals=[100,150,80,50]
    durs=[d*2 for d in [1,0.5,0.1,2]]
    pauses=list(reversed(durs))
    for v,d,p in zip(vals,durs,pauses):
        lc.pulse(1,v,d,0.5)
        time.sleep(p)
