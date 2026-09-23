## Copyright (C) 2026 - 2026 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

## AI-Assisted

## ClusterFuzzLite Python Dockerfile.
## https://google.github.io/clusterfuzzlite/build-integration/python-lang/

## Image: gcr.io/oss-fuzz-base/base-builder-python -- the canonical Python base
## for OSS-Fuzz / ClusterFuzzLite, published by Google's OSS-Fuzz project. The
## language guide tells integrators to use this exact path:
##   https://github.com/google/oss-fuzz/tree/master/infra/base-images/base-builder-python
##   https://google.github.io/oss-fuzz/getting-started/new-project-guide/python-lang/
##
## The digest is kept IN SYNC across our packages (privleap, helper-scripts et
## al.): :latest stays matched to clusterfuzzlite-run-fuzzers:v1's ABI (Ubuntu
## 20.04 / glibc 2.31), so binaries built here land cleanly in the run
## container. Do not pin to an ubuntu-24-04 tag without also forking CFLite's run
## image (see google/clusterfuzzlite#145 / #146). Refresh via a single digest
## swap when OSS-Fuzz republishes :latest at a new ABI.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:9dd557a4ba0e0cdfbeabc0bb115c98896f2dab68c3e8f301abf169469b8b5ef5

## No portable-CPython drop-in: sdwdate's parsers (url_to_unixtime, config.py)
## and the harnesses are plain 3.x, so the base's Python 3.11 parses and bundles
## them cleanly. (privleap needs a 3.12 drop-in only for its PEP 701 f-strings.)

## The fuzz harnesses + corpus live in org-ai-assisted/dist-ai (the single
## source for sdwdate's test/fuzz logic), NOT this package. Clone them at build
## time: the CFLite build context is this repo's git tree, so a workspace
## checkout never reaches the COPY below. dist-ai is public; @master per the
## org's branch-tracking model for our own cross-repo refs. build.sh compiles
## the SAME atheris harnesses the in-process sdwdate-tests-fuzz-atheris runs.
RUN git clone --depth 1 --branch master \
      https://github.com/org-ai-assisted/dist-ai "$SRC/dist-ai"

COPY . $SRC/sdwdate
COPY .clusterfuzzlite/build.sh $SRC/build.sh
WORKDIR $SRC/sdwdate
