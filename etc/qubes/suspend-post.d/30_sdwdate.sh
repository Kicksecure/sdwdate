#!/bin/bash

## Copyright (C) 2017 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

#### meta start
#### project Whonix
#### category networking and time
#### description
## hook to run <code>/usr/libexec/sdwdate/suspend-post</code>
## in Qubes-Whonix.
#### meta end

set -e

/usr/libexec/sdwdate/suspend-post
