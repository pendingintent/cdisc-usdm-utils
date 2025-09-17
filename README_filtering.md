Summary of Best Practices
1. Always add --list-key id (or your stable key) when diffing large lists of object dictionaries; it dramatically reduces false noise and uncovers real per-object changes even after reordering.
2. Use --objects-only for a concise overview. Drop it to inspect the raw field-level paths.
3. Combine --object-id-filter with --json when you want structured consumption (e.g., CI gating, focused review).
4. Add --path-filter anchored (^prefix) for performance and focus when you know a subtree.

Key Points
- zsh treats [ and ] as glob pattern characters unless quoted/escaped
- The diff tool’s --path-filter isn’t a regex engine; it only understands simple substring matching plus optional anchors:
    - prefix = path starts with prefix
    - suffix$ = path ends with suffix
    - ^exact$ = exact match
    - Otherwise: substring match

Quoted (simplest):
```
usdm-utils diff files/pilot_LLZT_amendment_10SEP25.json files/pilot_LLZT_amendment_11SEP25.json \
  --list-key id \
  --path-filter '^/study/versions[0]/biomedicalConcepts'
```

Escaped brackets (if you prefer no quotes):
```
usdm-utils diff files/pilot_LLZT_amendment_10SEP25.json files/pilot_LLZT_amendment_11SEP25.json \
  --list-key id \
  --path-filter ^/study/versions\[0\]/biomedicalConcepts
```

Disable globbing for just that command (then restore):
```
set -o noglob
usdm-utils diff files/pilot_LLZT_amendment_10SEP25.json files/pilot_LLZT_amendment_11SEP25.json \
  --list-key id \
  --path-filter ^/study/versions[0]/biomedicalConcepts
set +o noglob
```

If you want only one specific concept index (e.g. 128):
```
usdm-utils diff files/pilot_LLZT_amendment_10SEP25.json files/pilot_LLZT_amendment_11SEP25.json \
  --list-key id \
  --path-filter '^/study/versions[0]/biomedicalConcepts[128]'
```

Multiple filters (logical OR) – repeat the flag:
```
usdm-utils diff files/pilot_LLZT_amendment_10SEP25.json files/pilot_LLZT_amendment_11SEP25.json \
  --list-key id \
  --path-filter '^/study/versions[0]/biomedicalConcepts[128]' \
  --path-filter '^/study/versions[0]/biomedicalConcepts[129]'
```

Want object-level only for that subtree:
```
usdm-utils diff files/pilot_LLZT_amendment_10SEP25.json files/pilot_LLZT_amendment_11SEP25.json \
  --list-key id \
  --objects-only \
  --path-filter '^/study/versions[0]/biomedicalConcepts'
  ```

Then focus on a single concept id:
```
usdm-utils diff files/pilot_LLZT_amendment_10SEP25.json files/pilot_LLZT_amendment_11SEP25.json \
  --list-key id \
  --objects-only \
  --object-id-filter BiomedicalConcept_12 \
  --path-filter '^/study/versions[0]/biomedicalConcepts'
```

Field-level details for that concept (drop objects-only, anchor index):
```
IDX=128  # replace with the index you discovered via jq
usdm-utils diff files/pilot_LLZT_amendment_10SEP25.json files/pilot_LLZT_amendment_11SEP25.json \
  --list-key id \
  --path-filter "^/study/versions[0]/biomedicalConcepts[$IDX]"
```

Quick jq to find index:
```
jq '.study.versions[0].biomedicalConcepts
    | to_entries[]
    | select(.value.id=="BiomedicalConcept_12")
    | {index:.key}' files/pilot_LLZT_amendment_11SEP25.json
```


Future Improvements:
- A convenience wrapper later (e.g. --focus-object BiomedicalConcept_12)
