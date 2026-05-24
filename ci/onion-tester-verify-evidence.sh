#!/bin/bash

## Copyright (C) 2026 - 2026 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

## AI-Assisted

## Verify the wayback URL in each newly-added onion entry's
## comment actually mentions the .onion hash (Comment_Field_Rules
## provenance check). Truly-added = present in HEAD but not in
## base.

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
curl_max_time=90
retry_attempts=4
inter_attempt_sleep=10
user_agent='Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0'

resolve_base() {
   local base

   base="${GITHUB_BASE_REF:-master}"
   if ! git rev-parse --verify "origin/${base}" >/dev/null 2>&1; then
      git fetch --no-tags --depth=200 origin "${base}"
   fi
   printf '%s\n' "${base}"
}

list_really_added() {
   local base base_hashes head_hashes

   base="${1}"
   base_hashes="$(git show "origin/${base}:${conf}" 2>/dev/null \
      | grep --only-matching --extended-regexp -- '[a-z2-7]{56}\.onion' \
      | sort --unique || true)"
   head_hashes="$(grep --only-matching --extended-regexp -- \
      '[a-z2-7]{56}\.onion' "${conf}" \
      | sort --unique || true)"
   comm -23 \
      <(printf '%s\n' "${head_hashes}") \
      <(printf '%s\n' "${base_hashes}")
}

archive_urls_for_host() {
   local host line wayback_urls archive_ph_urls

   host="${1}"
   line="$(grep --fixed-strings -- "${host}" "${conf}" | head --lines=1)"
   ## Two tiers of proof URL, tried in order:
   ##   1. wayback (web.archive.org)         - permanent archive
   ##   2. archive.ph (archive.today)        - permanent archive
   ## A live-URL tier (extracted from the wayback URL) was
   ## considered but rejected: it would let a PR-controlled comment
   ## (e.g. `web/2*/https://evil.example.com/...`) cause CI to fetch
   ## arbitrary external URLs. New entries whose wayback snapshot
   ## hasn't yet captured the hash should re-snapshot via
   ## https://web.archive.org/save/... before opening the PR.
   wayback_urls="$(printf '%s\n' "${line}" \
      | grep --only-matching --extended-regexp -- \
         'https://web\.archive\.org/web/[0-9]+/[^ "]+' || true)"
   archive_ph_urls="$(printf '%s\n' "${line}" \
      | grep --only-matching --extended-regexp -- \
         'https://archive\.ph/[A-Za-z0-9]+' || true)"
   if [ -n "${wayback_urls}" ]; then
      printf '%s\n' "${wayback_urls}"
   fi
   if [ -n "${archive_ph_urls}" ]; then
      printf '%s\n' "${archive_ph_urls}"
   fi
}

## Outer loop is load-bearing: wayback occasionally returns HTTP
## 200 with snapshot-calendar HTML when its CDN cached a near-
## miss. curl --retry only fires on transport / HTTP errors so it
## cannot detect "200 with wrong body"; the loop re-fetches when
## the body lacks the hash, with enough sleep to outlast wayback's
## ~5-10s negative cache.
fetch_and_grep_hash() {
   local hash archive_urls tmp_file attempt archive_url

   hash="${1}"
   archive_urls="${2}"
   tmp_file="/tmp/wb-${hash}.html"
   while IFS= read -r archive_url; do
      if [ -z "${archive_url}" ]; then
         continue
      fi
      for ((attempt = 1; attempt <= retry_attempts; attempt++)); do
         curl --max-time "${curl_max_time}" --silent --show-error --location \
            --user-agent "${user_agent}" \
            --output "${tmp_file}" -- "${archive_url}" 2>/dev/null || true
         if [ -s "${tmp_file}" ] \
            && grep --ignore-case -- "${hash}" "${tmp_file}" >/dev/null; then
            return 0
         fi
         sleep "${inter_attempt_sleep}"
      done
   done <<< "${archive_urls}"
   return 1
}

main() {
   local base really_added host hash archive_urls ok missing count

   base="$(resolve_base)"
   really_added="$(list_really_added "${base}")"

   ok=0
   missing=0
   count=0

   if [ -z "${really_added}" ]; then
      printf '%s\n' "No truly-added onion entries in this diff. Skipping."
   else
      count="$(printf '%s\n' "${really_added}" | wc --lines)"
      printf '%s\n' "## Verifying provenance for ${count} ADDED entr(ies)"
      printf '%s\n' "## (some archive URL in the comment must mention the .onion hash)"

      while IFS= read -r host; do
         if [ -z "${host}" ]; then
            continue
         fi
         hash="${host%.onion}"
         archive_urls="$(archive_urls_for_host "${host}")"
         if [ -z "${archive_urls}" ]; then
            printf '%s\n' "  NO-ARCHIVE     ${host}  (no wayback / archive.ph URL in comment)" >&2
            missing=$((missing + 1))
            continue
         fi
         if fetch_and_grep_hash "${hash}" "${archive_urls}"; then
            printf '%s\n' "  PROOF-OK       ${host}"
            ok=$((ok + 1))
         else
            printf '%s\n' "  PROOF-MISSING  ${host}  (hash not in any of: ${archive_urls//$'\n'/ })" >&2
            missing=$((missing + 1))
         fi
      done <<< "${really_added}"

      printf '%s\n' "Provenance summary: ${ok} verified, ${missing} unverified"
   fi

   if [ -n "${GITHUB_OUTPUT:-}" ]; then
      {
         printf 'added_count=%s\n' "${count}"
         printf 'verified=%s\n' "${ok}"
         printf 'missing=%s\n' "${missing}"
      } >> "${GITHUB_OUTPUT}"
   fi

   if [ "${missing}" -gt 0 ]; then
      printf '%s\n' "FAIL: ${missing} added onion(s) lack proof in their wayback URL." >&2
      printf '%s\n' "      Either the wayback URL doesn't include the .onion hash" >&2
      printf '%s\n' "      or it isn't a snapshot of the right page." >&2
      exit 1
   fi
}

main "${@}"
