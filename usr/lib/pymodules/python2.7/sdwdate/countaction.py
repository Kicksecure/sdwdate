# coding: utf-8

#  Copyright (C) 2014 Anthon van der Neut <anthon@mnt.org>
#  Copyright (C) 2014 Patrick Schleizer <adrelanos@riseup.net>
#  See the file COPYING for copying conditions.

import argparse


class CountAction(argparse.Action):
    """argparse action for counting up and down

    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action=CountAction, const=1,
                        nargs=0)
    parser.add_argument('--quiet', '-q', action=CountAction, const=-1,
                        nargs=0, dest='verbose',)
    """
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            val = getattr(namespace, self.dest) + self.const
        except TypeError:  # probably None
            val = self.const
        setattr(namespace, self.dest, val)
