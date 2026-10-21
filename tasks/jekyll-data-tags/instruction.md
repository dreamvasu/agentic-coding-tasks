Authors keep pasting reference tables and version strings into Markdown by hand, and they drift out of sync with the files under `_data/`. Add first-class `_data` rendering to this Jekyll checkout (the repo is at `/app`) so authors keep the source of truth in `_data/` and render it inline through a small family of Liquid tags. Once a value in `_data/` changes, every page that renders it must reflect the new value.

Implement these three tags:

- `{% data_table <name> %}` renders a `_data/<name>` collection (a list of maps) as an HTML `<table>`, with `columns: a,b,c` to choose which columns appear.
- `{% data_value <name>.<path> %}` inlines a single value from a `_data` file by dotted path, resolving nested maps (for example `site.release.version`), with an optional `default: "..."` for when the path is absent.
- `{% data_list <name> [field] %}` renders a `_data` collection as a `<ul>`; given a field name, it pulls just that field from each entry.

Follow how the codebase already handles Liquid tags (argument parsing, how tags resolve their inputs) so this feels native rather than bolted on. `/app/test_site/` has sample `_data/` and a page that already uses the tags; keep the public tag surface consistent with what is there. The three tags above are the full scope: implement them end to end and wire them in.
