We're migrating our CRM and I need to audit the exported customer phone list before it loads into the new system, which rejects the whole batch if any of the audit fields are off. The raw export is at `/app/contacts.csv` with columns `id`, `raw_number` (as the customer typed it, mostly in international `+` form with a few national formats), and `default_region` (a two-letter region code, filled in only for the rows entered without a country code). Parse each `raw_number` together with its `default_region`.

Write the audit to `/app/report.json` as a JSON object with exactly these fields:

- `total_numbers` — the number of rows in the file, as an integer.
- `valid_count` — how many of the numbers are valid, as an integer.
- `invalid_ids` — the sorted list of `id` values whose number is not valid.
- `type_histogram` — an object counting the valid numbers by line type, keyed by the uppercase type name (`"MOBILE"`, `"FIXED_LINE"`, `"FIXED_LINE_OR_MOBILE"`, `"VOIP"`, `"UAN"`, `"PREMIUM_RATE"`, `"SHARED_COST"`, `"TOLL_FREE"`, `"UNKNOWN"`, and so on). Include only the types that actually occur; if a valid number's type does not match a named category, key it under `"UNKNOWN"`.
- `carrier_by_id` — an object mapping the `id` of each valid number whose line type is `MOBILE` to the name of the network the number is allocated to, as a string (an empty string if no carrier is known). Numbers that are not valid `MOBILE` numbers are omitted.

The new system is strict about these fields, so each one has to be right. Write only the JSON object to `/app/report.json` and nothing else.
