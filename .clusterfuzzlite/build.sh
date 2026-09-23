#!/bin/bash

## Copyright (C) 2026 - 2026 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

## AI-Assisted

## ClusterFuzzLite build script. Invoked inside the OSS-Fuzz
## base-builder-python container by the ClusterFuzzLite tooling.
##
## Standard OSS-Fuzz contract:
##   - $SRC      - source root (the Dockerfile COPYs this repo to $SRC/sdwdate)
##   - $OUT      - output directory; harnesses go here
##   - compile_python_fuzzer - OSS-Fuzz helper that wraps a python harness into a
##                             runnable executable and copies it to $OUT/
##
## The fuzz HARNESSES + corpus are NOT kept in this package: they live in
## org-ai-assisted/dist-ai (the single source for sdwdate's test/fuzz logic,
## alongside every other sdwdate suite). The Dockerfile clones dist-ai to
## $SRC/dist-ai; this script compiles the SAME atheris harnesses the in-process
## sdwdate-tests-fuzz-atheris lane runs. The sdwdate subject still comes from
## THIS checkout, so the fuzzers test the code under review.
##
## NOTE: no CI-guard here. This script is invoked by ClusterFuzzLite inside the
## OSS-Fuzz base-builder container; it does not see the GitHub Actions CI=true
## env var. The trust boundary is the container itself, not this script.

## SRC / OUT / compile_python_fuzzer are provided by the OSS-Fuzz base-builder
## container, not assigned in this script (file-wide, before the first command).
# shellcheck disable=SC2154

set -o errexit
set -o nounset
set -o pipefail
set -o errtrace
shopt -s inherit_errexit
shopt -s shift_verbose
export LC_ALL=C

cd -- "${SRC}/sdwdate"

## The harnesses import dateutil + requests (url_to_unixtime) at load time;
## install them into the builder so pyinstaller can bundle them.
python3 -m pip install --quiet --no-cache-dir python-dateutil requests

## Harnesses + corpus from the dist-ai clone the Dockerfile placed at
## $SRC/dist-ai. sdwdate's config module is imported from THIS checkout.
tests_dir="${SRC}/dist-ai/usr/share/sdwdate-tests"
corpus_root="${tests_dir}/fuzz-corpus"
if [ ! -d "${tests_dir}" ]; then
  printf '%s\n' \
    "FATAL: ${tests_dir} missing; the Dockerfile must clone dist-ai to" \
    "${SRC}/dist-ai before this runs." >&2
  exit 1
fi

## sdwdate.config comes from THIS checkout; sdwdate_testlib from the dist-ai test
## dir. Both must be importable by the harnesses and bundlable by pyinstaller.
export PYTHONPATH="${SRC}/sdwdate/usr/lib/python3/dist-packages:${tests_dir}${PYTHONPATH+:${PYTHONPATH}}"

## fuzz_sdwdate_config: imports sdwdate.config as a module.
## --collect-submodules=sdwdate pins the package into the bundle (imported
## inside atheris.instrument_imports); --paths lets pyinstaller find
## sdwdate_testlib.
compile_python_fuzzer "${tests_dir}/fuzz_sdwdate_config.py" \
  --collect-submodules=sdwdate \
  --paths="${tests_dir}"

## fuzz_url_to_unixtime: the subject is the url_to_unixtime BIN script, loaded by
## path at runtime. The run container has no sdwdate checkout, so bundle the REAL
## script as data under sdwdate_bin/; the harness resolves it via _MEIPASS
## (still the real subject, never a reimplementation). --collect-submodules pins
## the parser deps the harness imports inside instrument_imports.
compile_python_fuzzer "${tests_dir}/fuzz_url_to_unixtime.py" \
  --add-data="${SRC}/sdwdate/usr/bin/url_to_unixtime:sdwdate_bin" \
  --collect-submodules=dateutil \
  --collect-submodules=requests

## Seed corpus + dictionary per harness: meaningful starting inputs and keyword
## tokens so libFuzzer reaches deep parser branches from the first run.
## (Cross-run corpus growth is handled by ClusterFuzzLite's own storage.)
for name in fuzz_sdwdate_config fuzz_url_to_unixtime; do
  if [ -d "${corpus_root}/seeds/${name}" ]; then
    ## zip has no end-of-options '--'; OUT is a fixed container path (no dash).
    ( cd -- "${corpus_root}/seeds/${name}" \
        && zip --quiet --recurse-paths \
             "${OUT}/${name}_seed_corpus.zip" . )
  fi
  if [ -f "${corpus_root}/dicts/${name}.dict" ]; then
    cp -- "${corpus_root}/dicts/${name}.dict" "${OUT}/${name}.dict"
    printf '[libfuzzer]\ndict = %s.dict\n' "${name}" \
      > "${OUT}/${name}.options"
  fi
  printf 'compiled %s\n' "${name}"
done
