# Data provenance and licences

`contracts.json` holds 175 Solidity contracts derived from two public repositories, with all comments stripped,
long interior whitespace runs collapsed and blank lines collapsed (see `build_dataset.py`). Each record has
`id`, `source`, `label`, `label_class`, `all_classes`, `code`, `raw_len` and `sha1` (SHA-1 of the original file).

| Part | Source | Commit | Licence |
|---|---|---|---|
| 143 vulnerable contracts | SmartBugs-curated, https://github.com/smartbugs/smartbugs-curated | `230e649123477eff332742a59a1c7cc6dc286cab` | Apache License 2.0 (`third_party_licenses/smartbugs-curated_LICENSE_Apache-2.0`) |
| 32 patched ("safe") contracts | SWC Registry, `*_fixed.sol` samples in `entries/docs/SWC-*.md`, https://github.com/SmartContractSecurity/SWC-registry | `1b6227074ecd180b374e4844153afdda0332f979` | MIT (`third_party_licenses/SWC-registry_LICENSE_MIT`) |

The contract code remains under these upstream licences; this repository's MIT licence covers the code written
for this study. Modifications: comments removed and whitespace normalised; labels derived from the SmartBugs
folder / `vulnerabilities.json` (vulnerable) and set to `none` for SWC fixed samples. To rebuild the file from the
upstream repositories, run `REBUILD_DATA=1 ./run_all.sh` (first step only) or clone both repositories at the commits
above and run `python build_dataset.py`.
