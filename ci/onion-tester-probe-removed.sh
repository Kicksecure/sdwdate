#!/bin/bash

## Copyright (C) 2026 - 2026 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

## AI-Assisted

## Probe every onion the PR removes and fail if any is still
## reachable over Tor. "Really removed" = hash no longer appears
## anywhere in HEAD's conf (so pool moves, re-indents, and comment
## refreshes do not trigger).

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

conf='etc/sdwdate.d/30_default.conf'
proxy='127.0.0.1:9050'
curl_max_time=60

resolve_base() {
   local base

   base="${GITHUB_BASE_REF:-master}"
   if ! git rev-parse --verify "origin/${base}" >/dev/null 2>&1; then
      git fetch --no-tags --depth=200 origin "${base}"
   fi
   printf '%s\n' "${base}"
}

list_really_removed() {
   local base removed_urls current_hashes url hash

   base="${1}"
   ## Capture the FULL URL (with scheme + optional port) from each
   ## '-' line in the diff. Keeping the scheme matters: probing
   ## http:// for an entry that was https://-only would falsely
   ## report OFFLINE and greenlight a still-live removal. Same for
   ## the explicit-port form (e.g. `http://X.onion:8080/`).
   removed_urls="$(git diff "origin/${base}...HEAD" -- "${conf}" \
      | grep --only-matching --extended-regexp -- \
         '^-[[:space:]]+"http[s]?://[a-z2-7]{56}\.onion(:[0-9]+)?' \
      | sed -E 's/^-[[:space:]]+"//' \
      | sort --unique || true)"
   current_hashes="$(grep --only-matching --extended-regexp -- \
      '[a-z2-7]{56}\.onion' "${conf}" \
      | sort --unique || true)"
   while IFS= read -r url; do
      if [ -z "${url}" ]; then
         continue
      fi
      hash="$(printf '%s' "${url}" \
         | grep --only-matching --extended-regexp -- '[a-z2-7]{56}\.onion' || true)"
      if [ -z "${hash}" ]; then
         continue
      fi
      ## "Really removed" = hash absent from HEAD's conf. A pure
      ## scheme change (http -> https) keeps the hash, so the entry
      ## is not flagged.
      if printf '%s\n' "${current_hashes}" \
         | grep --line-regexp --fixed-strings -- "${hash}" >/dev/null; then
         continue
      fi
      printf '%s\n' "${url}"
   done <<< "${removed_urls}"
}

probe_one() {
   local url code

   url="${1}"
   case "${url}" in
      */)
         ;;
      *)
         url="${url}/"
         ;;
   esac
   code="$(curl --socks5-hostname "${proxy}" --max-time "${curl_max_time}" \
      --output /dev/null --silent --write-out '%{http_code}' \
      -- "${url}" 2>/dev/null || true)"
   code="${code:-000}"
   if [ "${code}" = "000" ]; then
      printf '%s\n' "  OFFLINE          ${url}"
      return 0
   fi
   printf '%s\n' "  ONLINE (HTTP ${code}) ${url}  <- UNEXPECTED" >&2
   return 1
}

main() {
   local base really_removed url alive count

   base="$(resolve_base)"
   really_removed="$(list_really_removed "${base}")"

   if [ -z "${really_removed}" ]; then
      printf '%s\n' "No truly-removed onion entries in this diff. Skipping."
      count=0
      alive=0
   else
      count="$(printf '%s\n' "${really_removed}" | wc --lines)"
      printf '%s\n' "## Probing ${count} REMOVED entr(ies) (must be OFFLINE)"

      alive=0
      while IFS= read -r url; do
         if [ -z "${url}" ]; then
            continue
         fi
         probe_one "${url}" || alive=$((alive + 1))
      done <<< "${really_removed}"
   fi

   if [ -n "${GITHUB_OUTPUT:-}" ]; then
      printf 'removed_count=%s\n' "${count}" >> "${GITHUB_OUTPUT}"
      printf 'still_alive=%s\n' "${alive}" >> "${GITHUB_OUTPUT}"
   fi

   if [ "${alive}" -gt 0 ]; then
      printf '%s\n' "FAIL: ${alive} 'removed' onion(s) are still reachable over Tor." >&2
      printf '%s\n' "      The PR claims to drop them as dead mirrors - revisit." >&2
      exit 1
   fi
}

main "${@}"
