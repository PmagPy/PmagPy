#!/usr/bin/env python
"""
Refresh PmagPy's cached copies of MagIC's rules and summarize what changed.

Run weekly by .github/workflows/magic-rules-sync.yml, which opens a pull
request with the summary when the rules change. It can also be run by hand
from the root of the repository:

    python .github/scripts/sync_magic_rules.py --summary summary.md

It
- downloads the MagIC data model, method codes and controlled and suggested
  vocabularies into pmagpy/data_model (magic_validation.update_cache), or
  into --cache-dir;
- writes a Markdown summary of the changes: columns, validation rules, method
  codes and vocabulary items added or removed, and which removed items
  PmagPy's code still uses;
- checks whether MagIC's parser or validator (the JavaScript that
  pmagpy/magic_validation.py ports) changed since the ported commit, and if
  so writes a report for an issue (--validator-report).

When run in GitHub Actions it sets the step outputs "changed" and
"validator_changed" to "true" or "false".
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from pmagpy import magic_validation as mv  # noqa: E402

GITHUB_API = "https://api.github.com/repos/earthref/MagIC"
SHOWN = 40  # longest list shown in full in the summary


def load(directory):
    return {name: mv.read_cached_resource(name, directory) for name in mv.RESOURCES}


def columns(model):
    return {(t, c): spec for t, table in model["tables"].items() for c, spec in table["columns"].items()}


def codes(method_codes):
    return {c["code"]: c.get("definition", "") for group in method_codes.values() for c in group["codes"]}


def items(vocabularies):
    return {name: {str(i["item"]) for i in v["items"]} for name, v in vocabularies.items()}


def listing(values):
    values = sorted(values)
    text = ", ".join("`{}`".format(v) for v in values[:SHOWN])
    if len(values) > SHOWN:
        text += ", and {} more".format(len(values) - SHOWN)
    return text


def used_in_pmagpy(names):
    """name -> files of PmagPy's Python code that use it as a whole word or quoted string."""
    # one- and two-character names (e.g. the old booleans "t" and "f") match everywhere
    names = sorted({n for n in names if len(n) > 2}, key=len, reverse=True)
    if not names:
        return {}
    files = subprocess.run(["git", "ls-files", "*.py"], cwd=ROOT, capture_output=True, text=True,
                           check=True).stdout.split()
    pattern = re.compile(r"(?<![\w.-])(" + "|".join(re.escape(n) for n in names) + r")(?![\w-])")
    found = {}
    for path in files:
        if path.startswith((".github/", "pmagpy_tests/")):
            continue
        try:
            with open(os.path.join(ROOT, path), encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        for match in set(pattern.findall(text)):
            found.setdefault(match, []).append(path)
    return found


def summarize(old, new):
    """Markdown lines describing the differences between two sets of cached rules."""
    lines = ["Weekly refresh of the MagIC rules cached in `pmagpy/data_model` "
             "(made by `.github/workflows/magic-rules-sync.yml`). Review the changes below before merging; "
             "removed items that PmagPy still uses need code changes, and newly required columns belong "
             "in the release notes.", ""]
    removed_names = []

    # the data model
    om, nm = old["data_model"], new["data_model"]
    lines += ["## Data model", "",
              "Updated day: {} → {}".format(om.get("updated_day", "?"), nm.get("updated_day", "?")), ""]
    oc, nc = columns(om), columns(nm)
    tables_added = set(nm["tables"]) - set(om["tables"])
    tables_removed = set(om["tables"]) - set(nm["tables"])
    if tables_added:
        lines.append("- **Tables added:** " + listing(tables_added))
    if tables_removed:
        lines.append("- **Tables removed:** " + listing(tables_removed))
    added = ["{}.{}".format(t, c) for t, c in set(nc) - set(oc)]
    removed = ["{}.{}".format(t, c) for t, c in set(oc) - set(nc)]
    if added:
        lines.append("- **Columns added ({}):** {}".format(len(added), listing(added)))
    if removed:
        lines.append("- **Columns removed ({}):** {}".format(len(removed), listing(removed)))
        removed_names += [c for _, c in set(oc) - set(nc) if c not in {c2 for _, c2 in nc}]
    newly_required, changed_rules = [], []
    for key in sorted(set(oc) & set(nc)):
        o, n = oc[key], nc[key]
        ov, nv = o.get("validations") or [], n.get("validations") or []
        name = "{}.{}".format(*key)
        if "required()" in nv and "required()" not in ov:
            newly_required.append(name)
        if ov != nv or o.get("type") != n.get("type"):
            change = "`{}`: ".format(name)
            if o.get("type") != n.get("type"):
                change += "type {} → {}; ".format(o.get("type"), n.get("type"))
            if ov != nv:
                change += "{} → {}".format(", ".join(ov) or "no rules", ", ".join(nv) or "no rules")
            changed_rules.append(change)
    for key in sorted(set(nc) - set(oc)):
        if "required()" in (nc[key].get("validations") or []):
            newly_required.append("{}.{} (new column)".format(*key))
    if newly_required:
        lines.append("- **Newly required ({}):** {}".format(len(newly_required), listing(newly_required)))
    if changed_rules:
        lines += ["- **Rules or types changed ({}):**".format(len(changed_rules)), "",
                  "<details><summary>show</summary>", ""]
        lines += ["  - " + c for c in changed_rules]
        lines += ["", "</details>"]
    if not (tables_added or tables_removed or added or removed or changed_rules):
        lines.append("- No changes to tables, columns or rules"
                     + (" (other content changed, e.g. descriptions)" if om != nm else "") + ".")
    lines.append("")

    # method codes
    oc_, nc_ = codes(old["method_codes"]), codes(new["method_codes"])
    lines += ["## Method codes", "", "{} → {} codes".format(len(oc_), len(nc_)), ""]
    if set(nc_) - set(oc_):
        lines.append("- **Added:** " + listing(set(nc_) - set(oc_)))
    if set(oc_) - set(nc_):
        lines.append("- **Removed:** " + listing(set(oc_) - set(nc_)))
        removed_names += list(set(oc_) - set(nc_))
    redefined = [c for c in set(oc_) & set(nc_) if oc_[c] != nc_[c]]
    if redefined:
        lines.append("- **Definitions changed:** " + listing(redefined))
    if old["method_codes"] == new["method_codes"]:
        lines.append("- No changes.")
    lines.append("")

    # vocabularies
    for key, title in (("vocabularies", "Controlled vocabularies"),
                       ("suggested_vocabularies", "Suggested vocabularies")):
        ov, nv = items(old[key]), items(new[key])
        lines += ["## " + title, ""]
        if ov == nv:
            lines += ["- No changes" + (" to the items (other content changed, e.g. labels)."
                                       if old[key] != new[key] else "."), ""]
            continue
        if set(nv) - set(ov):
            lines.append("- **Vocabularies added:** " + listing(set(nv) - set(ov)))
        if set(ov) - set(nv):
            lines.append("- **Vocabularies removed:** " + listing(set(ov) - set(nv)))
        for name in sorted(set(ov) & set(nv)):
            gained, lost = nv[name] - ov[name], ov[name] - nv[name]
            if gained or lost:
                parts = []
                if gained:
                    parts.append("added {}".format(listing(gained)))
                if lost:
                    parts.append("removed {}".format(listing(lost)))
                    if key == "vocabularies":
                        removed_names += list(lost)
                lines.append("- `{}`: {}".format(name, "; ".join(parts)))
        lines.append("")

    # removed items still in PmagPy's code
    used = used_in_pmagpy(removed_names)
    lines += ["## Removed items PmagPy's code still uses", ""]
    if used:
        for name in sorted(used):
            lines.append("- `{}`: {}".format(name, ", ".join("`{}`".format(p) for p in sorted(used[name])[:5])))
        lines += ["", "Check each use (a match can be a coincidence, e.g. a column name that is also an "
                      "ordinary word)."]
    else:
        lines.append("- None found.")
    return lines


def validator_changes():
    """(files changed, compare URL) for MagIC's parser and validator since the ported commit."""
    import requests
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    response = requests.get("{}/compare/{}...main".format(GITHUB_API, mv.MAGIC_PORTED_COMMIT), headers=headers,
                            timeout=30)
    response.raise_for_status()
    data = response.json()
    changed = [f["filename"] for f in data.get("files", []) if f["filename"] in mv.MAGIC_VALIDATOR_FILES]
    return changed, data.get("html_url", "")


def set_output(name, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.write("{}={}\n".format(name, value))
    print("{}={}".format(name, value))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cache-dir", default=mv.cache_dir(), help="the cached rules (default pmagpy/data_model)")
    parser.add_argument("--summary", default="magic_rules_summary.md", help="the Markdown summary to write")
    parser.add_argument("--validator-report", default="magic_validator_report.md",
                        help="the issue text to write if MagIC's validator changed")
    args = parser.parse_args()

    paths = [os.path.join(args.cache_dir, filename) for _, _, filename in mv.RESOURCES.values()]
    original = {}
    for path in paths:
        with open(path, "rb") as f:
            original[path] = f.read()
    old = load(args.cache_dir)
    mv.update_cache(args.cache_dir)
    new = load(args.cache_dir)
    changed = old != new
    if changed:
        with open(args.summary, "w", encoding="utf-8") as f:
            f.write("\n".join(summarize(old, new)) + "\n")
    else:
        # the same rules: keep the files byte for byte, so there is nothing to commit
        for path, content in original.items():
            with open(path, "wb") as f:
                f.write(content)
    set_output("changed", "true" if changed else "false")

    files, url = validator_changes()
    if files:
        with open(args.validator_report, "w", encoding="utf-8") as f:
            f.write("\n".join([
                "MagIC changed the JavaScript that `pmagpy/magic_validation.py` ports, since the ported commit "
                "`{}`:".format(mv.MAGIC_PORTED_COMMIT[:7]), ""]
                + ["- `{}`".format(p) for p in files]
                + ["", "Changes: {}".format(url), "",
                   "Port the changes to `magic_validation.py`, then set `MAGIC_PORTED_COMMIT` to the new commit "
                   "(and the commit named in the module docstring). Found by "
                   "`.github/workflows/magic-rules-sync.yml`."]) + "\n")
    set_output("validator_changed", "true" if files else "false")


if __name__ == "__main__":
    main()
