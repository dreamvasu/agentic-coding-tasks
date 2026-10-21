#!/bin/bash
set -euo pipefail

# Reference oracle: install the three _data-driven Liquid tags into the repo's
# tags directory, where `require_all "jekyll/tags"` (lib/jekyll.rb) auto-loads
# them. Each tag renders its _data source AND registers the rendering page's
# dependency on the backing _data file via site.regenerator.add_dependency,
# exactly as lib/jekyll/tags/include.rb does for includes -- so an incremental
# rebuild after a _data edit re-renders the page instead of serving stale output.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST=/app/lib/jekyll/tags

cp "$SCRIPT_DIR/tags/data_value.rb" "$DEST/data_value.rb"
cp "$SCRIPT_DIR/tags/data_table.rb" "$DEST/data_table.rb"
cp "$SCRIPT_DIR/tags/data_list.rb" "$DEST/data_list.rb"
