# coding: utf-8

#  Copyright (C) 2014 Anthon van der Neut <anthon@mnt.org>
#  Copyright (C) 2014 Patrick Schleizer <adrelanos@riseup.net>
#  See the file COPYING for copying conditions.

from __future__ import print_function

import os
import time

import ctypes
from ctypes import Structure, c_int, c_long, c_void_p, pointer

libc = ctypes.CDLL('librt.so.1')
libc.adjtimex.argtypes = [c_void_p]

nanoseconds_per_seconds = 1000000000


class TimeSpec(Structure):
    _fields_ = [
        ("tv_sec", c_long),         # seconds
        ("tv_nsec", c_long),        # nanoseconds
    ]


class ClockSetTime(TimeSpec):
    def __call__(self, clk_id, seconds, ns):
        assert abs(ns) < nanoseconds_per_seconds
        return self._no_check(clk_id, seconds, ns)

    def ns(self, ns, clk_id=0):
        return self._no_check(clk_id,
                              ns // nanoseconds_per_seconds,
                              ns % nanoseconds_per_seconds)

    def _no_check(self, clk_id, seconds, ns):
        self.tv_sec = c_long(seconds)
        print('self.tv_sec', self.tv_sec)
        self.tv_nsec = c_long(ns)
        print('self.tv_nsec', self.tv_nsec)
        return libc.clock_settime(c_int(clk_id), pointer(self))

clock_settime = ClockSetTime()


class ClockGetTime(TimeSpec):
    def __call__(self, clk_id=0):
        res = libc.clock_gettime(c_int(clk_id), pointer(self))
        return self.tv_sec, self.tv_nsec

    def ns(self, clk_id=0, v=None):
        s, ns = self() if v is None else v
        return s * nanoseconds_per_seconds + ns

    def str(self, v=None):
        if v is None:
            v = self()
        return 'time: {}.{:09d}'.format(*v)

clock_gettime = ClockGetTime()
