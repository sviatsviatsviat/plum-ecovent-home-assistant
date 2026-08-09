---
name: ci-pins
description: Keep GitHub Actions, Python packages, and Dev Container dependencies exactly pinned and synchronized across the repository. Use when editing requirements-dev.txt, .github/workflows, bumping actions, or reviewing CI config.
---

# CI and tool pins

All workflow `uses:` values must be exact pins. Tool versions in workflow commands, Dev Container features, `requirements-dev.txt`, and installation documentation must also be exact. Do not use `@latest`, branches, or floating major/minor tags.

When bumping one dependency:

1. locate every reference with `rg`;
2. update all references to that dependency in the same change;
3. preserve unrelated pins unless compatibility requires another bump;
4. run the workflow-tag audit;
5. run the normal repository verification when config affects installs/tests.

Examples of synchronized references:

- `homeassistant` / `pytest-homeassistant-custom-component`: always bump together in `requirements-dev.txt` (and any workflow install steps). Dependabot groups them under `homeassistant` in `.github/dependabot.yml` for the same reason. When bumping the Home Assistant pin, also update `homeassistant` in `hacs.json` and the README minimum-version note.
- `ruff`: `requirements-dev.txt`, README/AGENTS verification mentions if version specific;
- GitHub CLI: `.devcontainer/devcontainer.json` feature `ghcr.io/devcontainers/features/github-cli` version pin;
- an Action: every `uses:` entry for that Action.

Allowed workflow `uses:` pins (after stripping optional YAML quotes and trailing comments):

- Exact `@vN.N.N` release tags (default for all Actions).
- `hacs/action@N.N.N` only (HACS publishes tags without a `v` prefix).
- `home-assistant/actions/hassfest@` followed by a full 40-character commit SHA only (that repo does not publish usable version tags for hassfest).

Reject floating tags (`@vN`, `@vN.N`), branches (`@main`, `@master`, `@develop`), `@latest`, digests-only refs outside the hassfest exception, and any other unversioned ref.

Audit with:

```bash
python - <<'PY'
from pathlib import Path
import re

uses_re = re.compile(
    r"^\s*uses:\s*[\"']?([^\"'\s#]+)[\"']?\s*(?:#.*)?$"
)
# Exclude hacs/action and hassfest from @vN.N.N; they use dedicated patterns.
exact_v = re.compile(
    r"^(?!hacs/action@)(?!home-assistant/actions/hassfest@)"
    r".+@v\d+\.\d+\.\d+$"
)
hacs_action = re.compile(r"^hacs/action@\d+\.\d+\.\d+$")
hassfest_sha = re.compile(
    r"^home-assistant/actions/hassfest@[0-9a-f]{40}$"
)
violations = []
for path in Path(".github/workflows").rglob("*.y*ml"):
    for i, line in enumerate(path.read_text().splitlines(), 1):
        match = uses_re.match(line)
        if not match:
            continue
        ref = match.group(1)
        if (
            exact_v.fullmatch(ref)
            or hacs_action.fullmatch(ref)
            or hassfest_sha.fullmatch(ref)
        ):
            continue
        violations.append(f"{path}:{i}: {ref}")
if violations:
    print("\n".join(violations))
    raise SystemExit(1)
print("ok: all workflow uses: pins are exact")
PY
```

The audit must print `ok` and exit 0. Any printed violation must be fixed in the same change.
