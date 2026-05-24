#!/bin/bash

## Copyright (C) 2026 - 2026 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

## AI-Assisted

## Run /usr/share/sdwdate/onion-tester with bounded retry. The
## upstream script exits non-zero if even one of 62 URLs is
## OFFLINE - a stricter check than production sdwdate (which
## samples 3 random URLs per pool and tolerates some misses).
## Without a retry wrapper, a single transient Tor circuit
## timeout fails CI on otherwise-healthy URL sets.

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

attempts=3
inter_attempt_sleep=15

main() {
   local attempt rc final_attempt=0

   for ((attempt = 1; attempt <= attempts; attempt++)); do
      printf '%s\n' "=== onion-tester attempt ${attempt}/${attempts} ==="
      rc=0
      /usr/share/sdwdate/onion-tester || rc=$?
      final_attempt="${attempt}"
      if [ "${rc}" -eq 0 ]; then
         printf '%s\n' "onion-tester passed on attempt ${attempt}"
         break
      fi
      printf '%s\n' "onion-tester attempt ${attempt} failed (rc=${rc})" >&2
      if [ "${attempt}" -lt "${attempts}" ]; then
         printf '%s\n' "retrying in ${inter_attempt_sleep}s..." >&2
         sleep "${inter_attempt_sleep}"
      fi
   done

   if [ -n "${GITHUB_OUTPUT:-}" ]; then
      {
         printf 'attempts=%s\n' "${final_attempt}"
         printf 'final_rc=%s\n' "${rc}"
      } >> "${GITHUB_OUTPUT}"
   fi

   exit "${rc}"
}

main "${@}"
