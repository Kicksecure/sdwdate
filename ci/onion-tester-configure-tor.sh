#!/bin/bash

## Copyright (C) 2026 - 2026 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

## AI-Assisted

## Append CI torrc directives and restart tor@default.

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

main() {
   ## ControlPort + CookieAuth* are load-bearing: sdwdate's
   ## timesanitycheck uses stem.connection.connect(); without a
   ## reachable control connection every probed URL falls back to
   ## REACHABLE-but-INVALID. Cookie group-readable + chmod o+r in
   ## wait-bootstrap.sh make it usable by the non-debian-tor runner.
   ## Log notice file is read by wait-bootstrap.sh's grep.
   sudo tee --append /etc/tor/torrc > /dev/null <<'TORRC_EOF'

## Added by local-onion-tester.yml
ControlPort 9051
CookieAuthentication 1
CookieAuthFileGroupReadable 1
Log notice file /var/log/tor/notice.log
TORRC_EOF
   sudo systemctl restart tor@default
   printf '%s\n' "torrc appended; tor@default restarted"
}

main "${@}"
