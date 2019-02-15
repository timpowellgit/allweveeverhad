import DmxPy
import time
import random

### Settings you can set

# The probability of choosing each routine
ROUTINE_PROBS=[
        14, # rest
        26, # flash
        24, # ramp
        24, # continuous ramp
        12, # pulse
        ]

# The amount of time to wait between routines
ROUTINE_WAIT=[30,70]

# DMX channel number for light
LIGHT_DMX_CHAN=1

# Range of rest time values in seconds
REST_TIME_RANGE=[30,70]

# Global duration in seconds
GLOBAL_DUR=20

# Flash probability table as (number_of_flashes,probability) pairs
FLASH_PROBS=[(1,70),(2,25),(3,5)]

# Flash intensity range
FLASH_INTENSITY=[100,255]

# Flash duration coefficient range
FLASH_DUR=[0.5,2.0]

# Flash duration coefficient range (off time)
FLASH_OFF_DUR=[0.5,2.0]

# Ramp probabilities as (number_of_ramps,probability) pairs
RAMP_PROBS=[(1,50),(2,25),(3,15),(4,15)]

# Ramp duration coefficient range
RAMP_DUR=[0.5,2.0]

# Resolution of ramp steps in seconds
RAMP_RES=0.1

# Number of ramp segments
CONT_RAMP_SEGMENTS=[3,10]

# Random range for high values
CONT_RAMP_HIGH_RANGE=[120,255]

# Random range for low values
CONT_RAMP_LOW_RANGE=[30,50]

# Ramp time range
CONT_RAMP_TIME_RANGE=[1,30]

# Pulse duration coefficient range
PULSE_DUR=[0.5,2]

# Single pulse duration range (in milliseconds)
PULSE_SINGLE_DUR=[50,1000]

# Pulse intensity range
PULSE_INTENSITY=[120,255]

### Stuff below is just code

def weighted_choice(choices):
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w >= r:
            return c
        upto += w
    assert False, "Shouldn't get here"

class light_ctl_c(DmxPy.DmxPy):

    def __init__(self,serial_port,fastmode=0):
        self.fastmode = fastmode
        DmxPy.DmxPy.__init__(self,serial_port)

    def sleepseconds(self,secs):
        if (self.fastmode):
            time.sleep(secs*0.1) # for testing, so we don't wait forever
        else:
            time.sleep(secs)

    def send_val(self,chan,val):
        self.setChannel(chan,int(round(val)))
        self.render()

    def ramp(self,chan,val,dur,res):
        """
        Ramp from previous value at chan to val in dur seconds, incrementing
        each res seconds.
        if res > dur, the light will suddenly be at the value after dur
        If dur or res are 0 they are just made some small positive number
        """
        if dur == 0:
            dur = 1e-3
        if res == 0:
            res = 1e-3
        old_val=ord(self.dmxData[chan])
        inc=(val-old_val)/(dur/res)
        while (dur > 0):
            if res > dur:
                res = dur
                inc = val - old_val
            self.sleepseconds(res)
            old_val+=inc
            self.send_val(chan,old_val)
            dur -= res

    def pulse(self,chan,val,dur,ramp=0.1,ramp_res=0.01):
        """
            chan: channel to send on
            val: the value at the peak of the pulse
            dur: the total duration of the pulse including the ramps
            ramp: a ramp up / down at the beginning or end of the pulse (can
            be 0) in seconds. If 2*ramp>dur, we just force ramp to dur/2 and
            have no hold in the middle
            ramp_res: duration of the increments in seconds
        """
        if (2*ramp > dur):
            ramp=dur*0.5
        dur-=2*ramp
        old_val=ord(self.dmxData[chan])
        self.ramp(chan,val,ramp,ramp_res)
        self.sleepseconds(dur)
        self.ramp(chan,old_val,ramp,ramp_res)

class light_conductor_c(light_ctl_c):

    def rest(self,verbose=False):
        """
        Just do nothing for a time.
        """
        dur=random.uniform(*REST_TIME_RANGE)
        if (verbose):
            print " resting for %f seconds" % (dur,)
        self.sleepseconds(dur)

    def flash_routine(self,verbose=False):
        """
        Does the flashing routine.
        """
        nflashes = weighted_choice(FLASH_PROBS)
        if (verbose):
            print " flashing %d times" % (nflashes,)
        while nflashes > 0:
            nflashes -= 1
            v = random.uniform(*FLASH_INTENSITY)
            d = random.uniform(*FLASH_DUR) * GLOBAL_DUR
            if (verbose):
                print "  intensity %f, duration %f" % (v,d)
            self.pulse(LIGHT_DMX_CHAN,v,d)
            if (nflashes > 0):
                ot = random.uniform(*FLASH_OFF_DUR)
                if (verbose):
                    print "  sleeping %f seconds" % (ot,)
                self.sleepseconds(ot)

    def _ramp_shape_1(self,dur,verbose=False):
        """ up """
        if (verbose):
            print "ramp shape 1, dur %f" % (dur,)
        self.send_val(LIGHT_DMX_CHAN,0)
        self.ramp(LIGHT_DMX_CHAN,255,dur,res=RAMP_RES)
        self.send_val(LIGHT_DMX_CHAN,0)

    def _ramp_shape_2(self,dur,verbose=False):
        """ down """
        if (verbose):
            print "ramp shape 2, dur %f" % (dur,)
        self.send_val(LIGHT_DMX_CHAN,255)
        self.ramp(LIGHT_DMX_CHAN,0,dur,res=RAMP_RES)
        self.send_val(LIGHT_DMX_CHAN,0)

    def _ramp_shape_3(self,dur,verbose=False):
        """ saw shape """
        if (verbose):
            print "ramp shape 3, dur %f" % (dur,)
        self._ramp_shape_2(dur*0.5)
        self._ramp_shape_1(dur*0.5)

    def _ramp_shape_4(self,dur,verbose=False):
        """ "ASR" shape """
        if (verbose):
            print "ramp shape 4, dur %f" % (dur,)
        self.ramp(LIGHT_DMX_CHAN,255,dur/3,res=RAMP_RES)
        self.sleepseconds(dur/3)
        self.ramp(LIGHT_DMX_CHAN,0,dur/3,res=RAMP_RES)

    def ramp_routine(self,forceshape=None,verbose=False):
        """
        Does the ramping routine
        """
        nramps = weighted_choice(RAMP_PROBS)
        if forceshape:
            d = forceshape
        else:
            d = random.uniform(*RAMP_DUR) * GLOBAL_DUR
        rampshape = random.randint(1,4)
        for n in range(nramps):
            getattr(self,"_ramp_shape_%d" % (rampshape,))(d)
    
    def cont_ramp_routine(self,verbose=False):
        """
        Do a continuous ramp.
        """
        nsegs = random.randint(*CONT_RAMP_SEGMENTS)
        segvals = [((n+1)%2) * random.uniform(*CONT_RAMP_HIGH_RANGE) 
                + (n%2) * random.uniform(*CONT_RAMP_LOW_RANGE)
                for n in range(nsegs)]
        rtimes = [random.uniform(*CONT_RAMP_TIME_RANGE)
                for _ in range(nsegs)]
        if (verbose):
            print "doing continuous ramp with (vals,times)"
        for s,r in zip(segvals,rtimes):
            if (verbose):
                print " (%f,%f)" % (s,r)
            self.ramp(LIGHT_DMX_CHAN,s,r,RAMP_RES)
        self.send_val(LIGHT_DMX_CHAN,0)

    def pulse_routine(self,verbose=False):
        """
        Do many pulses at constant rate.
        """
        dur = random.uniform(*PULSE_DUR) * GLOBAL_DUR
        sdur = random.uniform(*PULSE_SINGLE_DUR) / 1000.
        i = random.uniform(*PULSE_INTENSITY)
        p = 1
        if (verbose):
            print ("doing pulses for %f seconds,"
                + " pulse dur %f, intensity %f") % (dur,sdur,i)

        while dur > 0:
            if p > 0:
                self.pulse(LIGHT_DMX_CHAN,i,sdur,ramp=dur*0.1)
            else:
                self.sleepseconds(sdur)
            p = 1 - p
            dur -= sdur

    def full_routine_iteration(self,verbose=False):
        routines=[
                self.rest,
                self.flash_routine,
                self.ramp_routine,
                self.cont_ramp_routine,
                self.pulse_routine,
                ]
        rout=weighted_choice(list(zip(routines,ROUTINE_PROBS)))
        rout(verbose)
        self.sleepseconds(random.uniform(*ROUTINE_WAIT))

    def test_routine(self):
        """
        Go through all the routines to see if they are working properly
        """
        print "testing rest"
        self.rest(verbose=True)
        print "testing flash_routine"
        self.flash_routine(verbose=True)
        for d in range(4):
            print "testing ramp_routine with shape %d" % (d,)
            self.ramp_routine(forceshape=d,verbose=True)
        print "testing cont_ramp_routine"
        self.cont_ramp_routine(verbose=True)
        print "testing pulse_routine"
        self.pulse_routine(verbose=True)

