#!/bin/bash
# Verifier: drive the real Jekyll incremental build and grade the HTML it emits.
# Pure Ruby/Jekyll using the image's system-wide Ruby/Bundler -- no Python. It
# restores a trusted page and _data files from heredocs first, so the agent cannot
# satisfy the check by editing the rendered page or the data fixtures; only the
# build output is graded. A clean build must render all three tags (FEATURE); an
# incremental rebuild after a _data edit must reflect the edit (INC) -- which holds
# only if the tags register the page's dependency on the _data file via
# site.regenerator.add_dependency, exactly as lib/jekyll/tags/include.rb does.
set -uo pipefail

mkdir -p /logs/verifier

SITE=/app/test_site
DATA="$SITE/_data"
mkdir -p "$DATA"

fail() { echo "VERIFIER-FAIL: $1" >&2; echo 0 > /logs/verifier/reward.txt; exit 0; }

# --- restore trusted page + _data (defeat page/data tampering) ---
cat > "$SITE/index.md" <<'PAGE'
---
title: Home
---
# {% data_value site.product %} {% data_value site.release.version %}

Tagline: {% data_value site.tagline default: "untitled" %}

{% data_table specs columns: name,limit %}

{% data_list specs name %}
PAGE

cat > "$DATA/site.yml" <<'SITEYML'
product: Acme
release:
  version: "2.4"
SITEYML

reset_specs() {
  cat > "$DATA/specs.yml" <<'SPECS'
- name: alpha
  tier: free
  limit: 10
- name: beta
  tier: pro
  limit: 100
SPECS
}
reset_specs

# --- pick the from-source Jekyll invocation (so the agent's lib/jekyll tags load) ---
cd /app
if bundle check >/dev/null 2>&1; then
  J=(bundle exec exe/jekyll)
else
  export JEKYLL_NO_BUNDLER_REQUIRE=true
  J=(ruby -Ilib exe/jekyll)
fi

clean()     { rm -rf "$SITE/_site" "$SITE/.jekyll-metadata" "$SITE/.jekyll-cache"; }
build_inc() { "${J[@]}" build --incremental -s "$SITE" -d "$SITE/_site" >/tmp/jekyll.log 2>&1; }
html()      { cat "$SITE/_site/index.html" 2>/dev/null; }

# --- FEATURE: a clean build renders all three tags from _data ---
clean; reset_specs
build_inc
H="$(html)"
echo "$H" | grep -q "Acme"     || { echo "=== build log ==="; tail -n 30 /tmp/jekyll.log >&2; fail "data_value site.product (Acme) did not render -- feature incomplete or non-building"; }
echo "$H" | grep -q "2.4"      || fail "data_value nested site.release.version (2.4) did not render"
echo "$H" | grep -q "untitled" || fail "data_value default (untitled) did not render"
echo "$H" | grep -q "<table>"  || fail "data_table did not render an HTML <table>"
echo "$H" | grep -q "alpha"    || fail "data_table/data_list did not render the specs data (alpha)"
echo "$H" | grep -q "<li>"     || fail "data_list did not render a <ul>/<li>"
echo "$H" | grep -q "free"     && fail "tier value 'free' leaked: data_table must honor 'columns: name,limit' and data_list must emit only the named field"
echo "$H" | grep -q "alpha_v2" && fail "clean build already shows alpha_v2 -- tag output is hardcoded, not derived from _data"

# --- INC (crux): edit a rendered _data value, rebuild incrementally ---
sed -i 's/name: alpha/name: alpha_v2/' "$DATA/specs.yml"
build_inc
H2="$(html)"
reset_specs
echo "$H2" | grep -q "alpha_v2" || { echo "=== INC stale (crux) build log ==="; tail -n 15 /tmp/jekyll.log >&2; fail "incremental rebuild served STALE output after a _data edit: the page's dependency on the _data file was not registered, so the regenerator did not re-render it"; }

echo 1 > /logs/verifier/reward.txt
echo "VERIFIER-PASS: all tags render and the incremental rebuild reflects the _data edit"
