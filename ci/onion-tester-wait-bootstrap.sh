#!/bin/bash

## Copyright (C) 2026 - 2026 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

## AI-Assisted

## Wait for Tor bootstrap, then chmod the control auth cookie
## world-readable so timesanitycheck (stem) can authenticate as
## the non-debian-tor runner user.

set -o errexit
set -o nounset
set -o pipefail
set -o errtrace
shopt -s inherit_errexit
shopt -s shift_verbose

if [ "${CI:-}" != "true" ] && [ "${ALLOW_LOCAL:-}" != "true" ]; then
   printf '%s\n' \
      "${BASH_SOURCE[0]}: refusing to run outside CI. Set ALLOW_LOCAL=true to override." >&2
   exit 1
fi

log_file='/var/log/tor/notice.log'
sleep_seconds=5
max_iterations=60

main() {
   local attempt

   for ((attempt = 1; attempt <= max_iterations; attempt++)); do
      if sudo grep 'Bootstrapped 100' "${log_file}" >/dev/null 2>&1; then
         printf '%s\n' "Bootstrapped after ~$((attempt * sleep_seconds))s"
         sudo tail --lines=3 -- "${log_file}"
         sudo chmod o+r /run/tor/control.authcookie || true
         exit 0
      fi
      sleep "${sleep_seconds}"
   done

   sudo tail --lines=30 -- "${log_file}" || true
   printf '%s\n' "FAIL: Bootstrap did not reach 100% within $((max_iterations * sleep_seconds))s" >&2
   exit 1
}

main "${@}"
