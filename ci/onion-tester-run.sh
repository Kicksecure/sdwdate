#!/bin/bash

## Copyright (C) 2026 - 2026 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

## AI-Assisted

## Run /usr/share/sdwdate/onion-tester with a bounded, targeted retry. The probe
## exits non-zero if even one of ~62 URLs is OFFLINE - a stricter check than
## production sdwdate (which samples 3 random URLs per pool and tolerates some
## misses). Without retry, a single transient Tor circuit timeout fails CI on an
## otherwise-healthy URL set.
##
## Design (why this shape):
##   * Attempt 1 probes the FULL conf. Each later attempt re-probes ONLY the URLs
##     that failed the previous one (the probe prints a 'FAILED_URL <url>' marker
##     per failure, and accepts a URL subset as arguments). A transient per-onion
##     flake thus costs a few-URL re-probe, not a full ~62-URL sweep -- far cheaper,
##     and it converges instead of re-rolling the whole set each time.
##   * A global WALL-CLOCK DEADLINE bounds the whole loop, and each attempt runs
##     under `timeout` with the remaining budget, so the wrapper always exits
##     cleanly (and records 'attempts') rather than being SIGKILL'd mid-probe by the
##     workflow step timeout (which loses the outputs). deadline < step cap.

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

## Overridable so the suite runs from a checkout / against a mock in tests; defaults
## to the installed probe.
onion_tester="${ONION_TESTER_BIN:-/usr/share/sdwdate/onion-tester}"
attempts="${ONION_TESTER_ATTEMPTS:-3}"
inter_attempt_sleep="${ONION_TESTER_RETRY_SLEEP:-15}"
## Wall-clock cap for the whole retry loop. MUST stay below the workflow step's
## timeout-minutes so we self-terminate and still emit outputs (default step cap is
## 18 min; 14 min here leaves margin for the inter-attempt sleeps + output).
deadline_seconds="${ONION_TESTER_DEADLINE:-840}"

main() {
   local start now elapsed remaining attempt rc final_attempt=0 tmp
   local -a probe_args=()

   start="$(date +%s)"
   tmp="$(mktemp)"
   rc=0

   for ((attempt = 1; attempt <= attempts; attempt++)); do
      now="$(date +%s)"
      elapsed=$((now - start))
      remaining=$((deadline_seconds - elapsed))
      if [ "${remaining}" -le 0 ]; then
         printf '%s\n' "onion-tester: wall-clock deadline (${deadline_seconds}s) reached before attempt ${attempt}; failing fast" >&2
         rc=124
         break
      fi

      if [ "${#probe_args[@]}" -eq 0 ]; then
         printf '%s\n' "=== onion-tester attempt ${attempt}/${attempts} (full conf; ${remaining}s of budget left) ==="
      else
         printf '%s\n' "=== onion-tester attempt ${attempt}/${attempts} (retry ${#probe_args[@]} failed URL(s); ${remaining}s left) ==="
      fi

      ## Bound the single attempt by the remaining budget; --kill-after reaps curl
      ## stragglers. Capture to ${tmp} to parse FAILED_URL markers, and cat it so the
      ## CI log still shows the full probe output.
      rc=0
      timeout --kill-after=10s "${remaining}s" "${onion_tester}" "${probe_args[@]}" > "${tmp}" 2>&1 || rc=$?
      cat -- "${tmp}"
      final_attempt="${attempt}"

      if [ "${rc}" -eq 0 ]; then
         printf '%s\n' "onion-tester passed on attempt ${attempt}"
         break
      fi
      if [ "${rc}" -eq 124 ]; then
         printf '%s\n' "onion-tester attempt ${attempt} hit the time budget (rc=124); failing fast" >&2
         break
      fi

      ## Narrow the next attempt to just the URLs that failed this one.
      mapfile -t probe_args < <(sed -n 's/^FAILED_URL //p' -- "${tmp}" | sort --unique)
      printf '%s\n' "onion-tester attempt ${attempt} failed (rc=${rc}); ${#probe_args[@]} URL(s) to retry" >&2
      if [ "${#probe_args[@]}" -eq 0 ]; then
         ## Non-zero but no parseable markers (e.g. the probe died before printing):
         ## keep the full set for the next attempt rather than silently narrowing to
         ## nothing (an empty arg list would re-probe the full conf anyway).
         printf '%s\n' "no FAILED_URL markers parsed; next attempt re-probes the full conf" >&2
      fi
      if [ "${attempt}" -lt "${attempts}" ]; then
         printf '%s\n' "retrying in ${inter_attempt_sleep}s..." >&2
         sleep "${inter_attempt_sleep}"
      fi
   done

   safe-rm --force -- "${tmp}"

   if [ -n "${GITHUB_OUTPUT:-}" ]; then
      {
         printf 'attempts=%s\n' "${final_attempt}"
         printf 'final_rc=%s\n' "${rc}"
      } >> "${GITHUB_OUTPUT}"
   fi

   exit "${rc}"
}

main "${@}"
