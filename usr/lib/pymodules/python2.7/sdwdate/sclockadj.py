# coding: utf-8

from __future__ import print_function

__version__ = "0.1.1"

import sys
import os
import argparse
import signal
import time
import subprocess
import errno

from getset_time import clock_gettime, clock_settime
from adjtimex import adjtime, dump_fields
from countaction import CountAction


class VPrint:
    """print depending on verbosity and level"""
    verbose = 0

    def __init__(self, level=0):
        self.level = level

    def __call__(self, *args, **kw):
        lvl = kw.pop('level', self.level)  # required level
        if self.verbose < lvl:
            return
        print(*args, **kw)

vprint = VPrint(level=1)  # print if verbose >= 1
nprint = VPrint()  # print if verbose >= 0


class SneakyClockAdjuster:
    def __init__(self):
        self.args = None
        self.subparsers = []

    def parse_args(self, cli_args=None):
        parser = argparse.ArgumentParser()

        offset = self.sub_parser(
            parser, 'offset', cmd=self.cmd_offset,
            help="change offset (requires UID=0)")
        offset.add_argument(
            "nanoseconds",  type=int,  # smart enough to handle -num
            help="Nanoseconds to add (substract if negative)",)
        offset.add_argument(
            "--constant",
            help="""0 -> fastest autoadjusted for nano/µ sec (default no
            adjustment)"""
        )

        status = self.sub_parser(
            parser, 'status', cmd=self.cmd_status,
            help="report adjtimex status",
            description="""adjtimex status (--quiet -> only offset,
            --verbose -> detail)""",
        )
        status.add_argument(
            "--follow", "-f", action="store_true",
            help="follow status indefinately"
        )
        status.add_argument(
            "--set", action="store_true",
            help="set status explicitly to PLL and NANO"
        )

        for sp in self.subparsers:
            sp.add_argument(
                '--verbose', '-v',
                help='increase verbosity level', action=CountAction,
                const=1, nargs=0, default=0)
            sp.add_argument(
                '--quiet', '-q',
                help='decrease verbosity level', action=CountAction,
                const=-1, nargs=0, default=0, dest='verbose')
            sp.add_argument(
                '--no-verbose',
                help=argparse.SUPPRESS, action=CountAction,
                const=-1, nargs=0, dest='verbose')
            sp.add_argument(
                '--debug', '-D', action='store_true',
                help="Debug messages. Don't change date",)
            sp.add_argument(
                '--no-debug', action='store_false', dest="debug",
                help=argparse.SUPPRESS,)
            sp.add_argument(
                "--wait", action='store_true',
                help="wait for offset to return to 0"
            )

        parser.add_argument('--version', action='version',
                            version='%(prog)s ' + __version__)
        self.args = args = parser.parse_args(args=cli_args)
        VPrint.verbose = self.args.verbose
        if self.args.debug and self.args.verbose < 1:
            self.args.verbose = 1

    def sub_parser(self, parser, name, help=None, description=None, cmd=None):
        # first sets up subparsers if necessary
        sps = getattr(self, '_subparsers', None)
        if sps is None:
            sps = self._subparsers = parser.add_subparsers(
                dest="subparser_name", help='sub-command help')
        sp = sps.add_parser(name, help=help, description=description)
        self.subparsers.append(sp)
        if cmd:
            sp.set_defaults(func=cmd)
        return sp

    def cmd_status(self):
        nprint('status', self.args, level=2)
        if self.args.set:
            if not adjtime.root:
                print("Have to be root to set time")
                return -1
            adjtime.modes = adjtime.adj.STATUS | adjtime.adj.NANO
            adjtime.status = adjtime.stat.PLL
            # _ = adjtime.nano
            print ('setting status', adjtime.status)
            res = adjtime.call()
        adjtime.modes = 0
        res = adjtime.call()
        if self.args.verbose < 0:
            return "{}".format(adjtime.offset)
        if self.args.wait or self.args.follow:
            while True:
                offset = adjtime.print_status()
                if self.args.wait and offset == 0:
                    return
                time.sleep(1)
                adjtime.update_status()
            return
        print('{}:'.format(os.path.basename(sys.argv[0])))
        print('  result:   {:4x} ({})'.format(res, adjtime.str_result(res)))
        print('  status: 0x{:4x} ({})'.format(adjtime.status,
                                                  adjtime.str_status()))
        print('  offset: {}'.format(adjtime.offset))
        if self.args.verbose > 0:
            print('  detail:')
            dump_fields(adjtime, sys.stdout)

    def cmd_offset(self):
        if not adjtime.root:
            vprint("Have to be root to set time")
            if not self.args.debug:
                return errno.EPERM
        vprint("Running with PID: {}".format(os.getpid()))
        if self.args.wait:
            signal.signal(signal.SIGTERM, self.signal_handler)
            signal.signal(signal.SIGINT, self.signal_handler)

        adjtime.verbose = self.args.verbose
        adjtime.debug = self.args.debug
        adjtime.test_state_ok()
        if adjtime.nano:
            adjtime.nanosec(self.args.nanoseconds, constant=self.args.constant,
                            wait=self.args.wait)
        else:
            micro, nano = divmod(self.args.nanoseconds, 1000)
            if micro < 0:  # divmod overshoots on negative numbers
                micro += 1
                nano -= 1000
            if nano:
                # do first, as we might not want to wait
                clock_settime.ns(clock_gettime.ns() + nano)
            adjtime.microsec(micro, constant=self.args.constant,
                             wait=self.args.wait)

    @staticmethod
    def signal_handler(signum, frame):
        print("Exiting...")
        if signum == signal.SIGTERM:
            sys.exit(143)
        if signum == signal.SIGINT:
            sys.exit(130)

    def run(self):
        if self.args.func:
            return self.args.func()


def main():
    n = SneakyClockAdjuster()
    args = None
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        args = [
            "--verbose",
            "--verbose",
            "-10765068147",
        ]
    n.parse_args(args)
    sys.exit(n.run())