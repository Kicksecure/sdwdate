# coding: utf-8

#  Copyright (C) 2014 Anthon van der Neut <anthon@mnt.org>
#  Copyright (C) 2014 Patrick Schleizer <adrelanos@riseup.net>
#  See the file COPYING for copying conditions.

from __future__ import print_function

import os
import sys
import errno
import time
import math

import ctypes
from ctypes import Structure, c_int, c_long, c_void_p, pointer

libc = ctypes.CDLL('libc.so.6')
libc.adjtimex.argtypes = [c_void_p]


class TimeVal(Structure):
    _fields_ = [
        ("tv_sec", c_long),         # seconds
        ("tv_usec", c_long),        # microseconds
    ]


class AdjTimex(Structure):
    _fields_ = [
        ("modes", c_int),         # mode selector
        ("offset", c_long),       # time offset (usec(, nanosec if in NANO mode
        ("freq", c_long),         # frequency offset (scaled ppm)
        ("maxerror", c_long),     # maximum error (usec)
        ("esterror", c_long),     # estimated error (usec)
        ("status", c_int),        # clock command/status
        ("constant", c_long),     # pll time constant
        ("precision", c_long),    # clock precision (usec) (read-only)
        ("tolerance", c_long),    # clock frequency tolerance (ppm) (read-only)
        ("time", TimeVal),        # current time (read-only)
        ("tick", c_long),         # usecs between clock ticks
        ("ppsfreq", c_long),      # pps frequency (scaled ppm) (ro)
        ("jitter", c_long),       # pps jitter (us) (ro)
        ("shift", c_int),         # interval duration (s) (shift) (ro)
        ("stabil", c_long),       # pps stability (scaled ppm) (ro)
        ("jitcnt", c_long),       # jitter limit exceeded (ro)
        ("calcnt", c_long),       # calibration intervals (ro)
        ("errcnt", c_long),       # calibration errors (ro)
        ("stbcnt", c_long),       # stability limit exceeded (ro)
        ("ai", c_int),            # TAI offset (ro)
    ]

    # MAXPHASE from timex.h, used to be 131071 in Linux 2.6
    max_time_microsec = 500000

    class Adj:
        OFFSET = 0x0001      # time offset
        FREQUENCY = 0x0002   # frequency offset
        MAXERROR = 0x0004    # maximum time error
        ESTERROR = 0x0008    # estimated time error
        STATUS = 0x0010      # clock status
        TIMECONST = 0x0020   # pll time constant
        TAI = 0x0080	    # set TAI offset
        SETOFFSET = 0x0100   # add 'time' to current time
        MICRO = 0x1000	    # select microsecond resolution
        NANO = 0x2000	    # select nanosecond resolution
        TICK = 0x4000	    # tick value

    adj = Adj()

    class Stat:
        PLL = 0x0001        # enable PLL updates (rw)
        PPSFREQ = 0x0002    # enable PPS freq discipline (rw)
        PPSTIME = 0x0004    # enable PPS time discipline (rw)
        FLL = 0x0008        # select frequency-lock mode (rw)
        INS = 0x0010        # insert leap (rw)
        DEL = 0x0020        # delete leap (rw)
        UNSYNC = 0x0040     # clock unsynchronized (rw)
        FREQHOLD = 0x0080   # hold frequency (rw)
        PPSSIGNAL = 0x0100  # PPS signal present (ro)
        PPSJITTER = 0x0200  # PPS signal jitter exceeded (ro)
        PPSWANDER = 0x0400  # PPS signal wander exceeded (ro)
        PPSERROR = 0x0800   # PPS signal calibration error (ro)
        CLOCKERR = 0x1000   # clock hardware fault (ro)
        NANO = 0x2000       # resolution (0 = us, 1 = ns) (ro)
        MODE = 0x4000       # mode (0 = PLL, 1 = FLL) (ro)
        CLK = 0x8000        # clock source (0 = A, 1 = B) (ro)

    stat = Stat()   # status name was already is taken by fields

    def call(self, verbose=0):
        # print('call {:x} {:x}'.format(self.modes, self.status)
        return libc.adjtimex(pointer(self))

    def str_result(self, res):
        if res < 0:
            return os.strerror(res)
        return [
            "synchronized, no leap second",
            "insert leap second",
            "delete leap second",
            "leap second in progress",
            "leap second has occurred",
            "clock not synchronized",
        ][res]

    def str_status(self):
        res = []
        for x in (x for x in dir(self.stat) if x[0] != '_'):
            if getattr(self.stat, x) & self.status:
                res.append(x)
        return ' | '.join(res)


def dump_fields(obj, fp, indent=4):
    prefix = ' ' * indent
    l = 0
    # attempt to display nicely
    for f, t in obj._fields_:
        if len(f) > l:
            l = len(f)
    l += 1
    for f, t in obj._fields_:
        v = getattr(obj, f)
        if hasattr(v, '_fields_'):
            print('{}{}:'.format(prefix, f))
            dump_fields(v, fp, indent+2)
            continue
        print('{}{:{}} {:>13}'.format(prefix, f+':', l, v))


class AdjTime(AdjTimex):
    def __init__(self):
        super(AdjTimex, self).__init__()
        self._verbose = 0
        self._debug = False
        self.root = os.getuid() == 0
        self._nano = None

    @property
    def nano(self):
        # property so you don't call adjtimex on import
        if self._nano is None:
            self.modes = self.adj.STATUS | self.adj.NANO
            self.status = self.stat.PLL
            res = self.call()
            assert res >= 0
            self.mode = 0
            res = self.call()
            print ("nano setting status {:x}".format(self.status))
            self._nano = self.status & self.stat.NANO
        return self._nano

    def update_status(self, mode=0):
        res = self.call()
        return res

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, val):
        self._verbose = val

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, val):
        self._debug = val

    def print_status(self, res=None, count=None):
        if res is not None:
            res = str(res) + ' '
        else:
            res = ''
        # 10 because of minus sign
        s = "{}({}) offset: {:>10} {}, const: {}".format(
            res,
            self.str_status(),
            self.offset,
            "ns" if self.status & self.adj.NANO else "µs",
            self.constant)
        if count is not None:
            s += ' [{}]'.format(count)
        print(s)
        return self.offset

    def test_state_ok(self):
        _ = self.nano  # to force initializing
        if self.verbose > 0:
            print("testing state")
        assert self.status & self.stat.PLL
        self.status = 0x0001
        self.modes = self.adj.STATUS
        # print(self.call(), self.get_status())
        if self.status & self.stat.FREQHOLD:
            if self.debug:
                print("  FREQHOLD set in adjtimex")
            else:
                self.status = 0x2001
                self.modes = self.adj.STATUS
                print(self.call())
                assert not (self.status & self.stat.FREQHOLD)

    def set_offset(self, offset, constant=None):
        if not self.root:
            raise NotImplementedError
        self.offset = offset
        self.modes = self.adj.OFFSET
        if constant is not None:
            self.constant = constant
            self.modes |= self.adj.TIMECONST
        return self.call()

    def track_until_zero_offset(self, offset, constant=None, verbose=0):
        res = self.set_offset(offset, constant=constant)
        if verbose > 0:
            print(adjtimex.offset, res)
        count = 0
        while True:
            if verbose > 0:
                self.print_status(res, count)
            if res < 0 or adjtimex.offset == 0:
                break
            time.sleep(1)
            adjtimex.modes = AdjTimex.adj.TIMECONST
            adjtimex.constant = -4
            adjtimex.call()
            count += 1

        adjtimex.status = 0x2001
        adjtimex.modes = adjtimex.adj.STATUS
        adjtimex.call()
        if verbose > 0:
            self.print_status(res, count)
        return count

    def print_remaining(self, loop_count, nr_loops, rest_time):
        """print the number of number and total number of loops (partial loops
        rounded up with the math.ceil() stuff) and an estimated amount of
        seconds left based on the length of the previous loop and the
        remaining partial loops. On first invocation rest_time is probalby
        a string: "unknown"
        """
        if isinstance(rest_time, (float, int)):
            # nr_loops is a float, loop_count one to high
            rest_time = (nr_loops - loop_count + 1) * rest_time
            rest_time = int(rest_time)
            rest_str = "{}s".format(rest_time)
            if rest_time > 59:
                rest_str += " ("
                h, rest_time = divmod(rest_time, 3600)
                if h:
                    rest_str += "{}h".format(h)
                m, rest_time = divmod(rest_time, 60)
                if h:
                    rest_str += "{:02}m".format(m)
                else:
                    rest_str += "{}m".format(m)
                rest_str += "{}s".format(rest_time)
                rest_str += ")"
        else:
            rest_str = rest_time
        # round the number of loops up for the final partial one
        print('0.5 second loop {}/{}, '
              'remaining time: {}'.format(
            loop_count, int(math.ceil(nr_loops)), rest_str))

    def microsec(self, offset, constant=None, pid=None):
        if constant is None:
            constant = 0
        self.nanosec(offset, constant=constant,
                     pid=pid, mt=self.max_time_microsec)

    def nanosec(self, offset, constant=None, pid=None, mt=None):
        if constant is None:
            constant = -4
        else:
            constant -= 4  # adjustment for nanoseconds
        if mt is None:
            mt = self.max_time_microsec * 1000
        max_step = mt if offset >= 0 \
            else -mt
        looping = True
        if not self.debug:
            assert self.root
        nr_loops = float(offset) / max_step
        loop_count = 0
        rest_time = "unknown"
        while looping:
            if pid:
                pid.check()
            start_time = time.time()
            if abs(offset) > mt:
                if pid is None:
                    if self.verbose > -1:
                        print('argument to big, use --wait')
                    sys.exit(errno.EINVAL)
                loop_count += 1
                if self.verbose > 0:
                    self.print_remaining(loop_count, nr_loops, rest_time)
                # always wait on max
                self._ns(max_step, constant=constant, wait=True)
            else:
                loop_count += 1
                if self.verbose > 0:
                    self.print_remaining(loop_count, nr_loops, rest_time)
                self._ns(offset, constant=constant, wait=pid is not None)
                looping = False
            rest_time = time.time() - start_time
            offset -= max_step
            if looping and pid:
                pid.check()

    def _ns(self, offset, constant, wait):
        if self.verbose > 1:
            print('this step', offset)
        # assumed to be in nanoseconds is ADJ_NANO in status
        self.offset = offset
        self.modes = self.adj.OFFSET
        if constant is not None:
            self.constant = constant
            self.modes |= self.adj.TIMECONST
        if not self.debug:
            res = self.call()
        else:
            res = 0
        count = 0
        while True:
            if not wait:
                break
            if res < 0 or self.offset == 0:
                break
            if self.verbose > 0:
                self.print_status(res, count)
            if self.debug:
                print("debug: exit loop")
            time.sleep(1)
            self.modes = AdjTimex.adj.TIMECONST
            self.constant = constant
            self.call()
            count += 1

        self.status = 0x1
        self.modes = self.adj.STATUS
        self.call()
        if self.verbose > 0:
            self.print_status(res, count)
        return count


adjtime = AdjTime()
