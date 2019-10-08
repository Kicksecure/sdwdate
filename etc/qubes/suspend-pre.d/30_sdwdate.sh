#!/bin/bash

## Copyright (C) 2017 - 2018 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

#### meta start
#### project Whonix
#### category networking and time
#### description
## hook to run <code>/usr/lib/sdwdate/suspend-pre</code>
## in Qubes-Whonix.
#### meta end

set -e

/usr/lib/sdwdate/suspend-pre
