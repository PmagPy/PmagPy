# Making pip releases

This walks through cutting a release of `pmagpy` and `pmagpy-cli` to PyPI.

## Prerequisites (one-time setup)

You need:

- Maintainer access to both projects on PyPI ([pmagpy](https://pypi.org/project/pmagpy/), [pmagpy-cli](https://pypi.org/project/pmagpy-cli/)) and on TestPyPI ([pmagpy](https://test.pypi.org/project/pmagpy/), [pmagpy-cli](https://test.pypi.org/project/pmagpy-cli/)).
- API tokens for both PyPI and TestPyPI. Generate at:
  - <https://pypi.org/manage/account/token/>
  - <https://test.pypi.org/manage/account/token/>
- A `~/.pypirc` configured with both. Example contents:

  ```ini
  [distutils]
  index-servers =
      pypi
      pypitest

  [pypi]
  username = __token__
  password = pypi-AgENd...your-real-pypi-token...

  [pypitest]
  repository = https://test.pypi.org/legacy/
  username = __token__
  password = pypi-AgENd...your-test-pypi-token...
  ```

  Note: `username = __token__` is literal — the actual credential goes in `password`. Real PyPI and TestPyPI tokens are not interchangeable.

- Up-to-date build tools (`twine` ≥ 5.0 is required for setuptools' Metadata-Version 2.4):

  ```bash
  pip install --upgrade build setuptools twine
  ```

## Pre-release checks

1. Run the test suite locally and ensure it passes.
2. Bump the version in [pmagpy/version.py](pmagpy/version.py).
3. Test the prospective release on the platforms users actually run on (see below).

## Testing a branch or the main repo from a platform like Colab

The primary release rehearsal is to install directly from GitHub via `pip install git+https://...`. This works in any environment with `pip` and `git` (including Google Colab) and exercises the same build-and-install path a published release would use, including resolution of `install_requires`. Crucially, real PyPI is untouched, so users on the currently-published version are not exposed during testing.

### Install from a feature branch (release rehearsal)

Use this when you have a PR open and want to verify the prospective release before merging. Replace `<branch-name>` with your branch:

```python
!pip install git+https://github.com/PmagPy/PmagPy.git@<branch-name>

import pmagpy
print('pmagpy:', pmagpy.__file__)

from pmagpy.coefficients import get_igrf14
models, coeffs = get_igrf14()
print('IGRF14 ok:', len(models), 'models, coeffs', coeffs.shape)

import pmagpy.pmag as pmag
import pmagpy.ipmag as ipmag
print('pmag and ipmag imported')
```

Then run a few of the typical functions you actually use (or that students rely on) to confirm nothing's broken under the new dependency resolution.

### Install from the main repo (latest development state)

Use this to share a development snapshot with collaborators or to reproduce a bug against `master`:

```python
!pip install git+https://github.com/PmagPy/PmagPy.git
```

If pip caches an older copy, force a fresh clone with:

```python
!pip install --upgrade --force-reinstall git+https://github.com/PmagPy/PmagPy.git
```

### Notes

- For `pmagpy-cli`, `pip install git+...` only sees `setup.py` (the `pmagpy` package) by default and won't build `pmagpy-cli` (which uses `command_line_setup.py`). For Colab-style usage this is rarely a concern — the GUI launchers in `pmagpy-cli` aren't typically run in a notebook.
- Restart the runtime if Colab prompts you to: pip may have upgraded or downgraded numpy/scipy/etc. when resolving the new `install_requires`, and the kernel needs to reload.

### What this misses (and when to also use TestPyPI)

The branch test catches code, dependency, and build-system problems, but it doesn't exercise PyPI itself. It will not surface things like:

- PyPI metadata validation rejecting the upload (e.g. PEP 625 sdist filename normalization on hyphenated names like `pmagpy-cli`).
- `twine upload` failures from a stale twine version that doesn't understand the Metadata-Version setuptools is writing.
- README rendering issues on the project page.

If you've changed packaging metadata or the project's build configuration, doing a TestPyPI upload (Stage 1 below) catches those. For pure code/dependency changes, the branch test is sufficient and TestPyPI can be skipped.

## Cut the release

Once the change is merged to `master`:

```bash
git checkout master
git pull
```

### Stage 1 — TestPyPI (optional)

Skip this stage if you only changed code or dependencies and the branch test above passed. Use it when you've changed packaging metadata, the build system, or anything that could affect what PyPI itself accepts (see "What this misses" above for examples). The upload exercises PyPI's own validation, so issues like PEP 625 filename rejection or README rendering errors surface here rather than during the real release.

```bash
rm -rf build dist && python setup.py sdist bdist_wheel && twine upload --repository pypitest dist/*
rm -rf build dist && python command_line_setup.py sdist bdist_wheel && twine upload --repository pypitest dist/*
```

Verify the project pages render at:

- <https://test.pypi.org/project/pmagpy/>
- <https://test.pypi.org/project/pmagpy-cli/>

### Stage 2 — Real PyPI

```bash
rm -rf build dist && python setup.py sdist bdist_wheel && twine upload dist/*
```

Verify at <https://pypi.org/project/pmagpy/> that the new version is live and the description renders. Then:

```bash
rm -rf build dist && python command_line_setup.py sdist bdist_wheel && twine upload dist/*
```

Verify at <https://pypi.org/project/pmagpy-cli/>.

PyPI does not allow re-uploading a file with the same name. If something goes wrong mid-upload, you cannot reupload — bump to a post-release suffix (e.g., `4.3.13.post1`) and try again.

### Stage 3 — Tag the commit and create a GitHub release

```bash
git tag -a v<version> -m "PmagPy <version>"
git push origin v<version>
```

Then on GitHub: **Releases → Draft a new release → choose tag → "Generate release notes" → Publish**. This creates a citable artifact and an auto-generated changelog for users.

## Common errors

### `400 Bad Request` from PyPI on the sdist of `pmagpy-cli`

PyPI enforces PEP 625 normalization: hyphenated names like `pmagpy-cli` must produce sdist filenames using underscores (`pmagpy_cli-X.Y.Z.tar.gz`), not hyphens. Older setuptools generates the hyphenated form and the upload is rejected. Fix by upgrading setuptools (≥ 69.3 produces the normalized filename) and rebuilding.

### `InvalidDistribution: Metadata is missing required fields: Name, Version`

Twine versions before 5.0 only understand Metadata-Version up to 2.2, but setuptools 69+ writes Metadata-Version 2.4. The error is misleading — the metadata is fine, twine just can't parse it. Upgrade twine:

```bash
pip install --upgrade twine
```

### `403 Forbidden` from TestPyPI

Most often a credentials problem: TestPyPI tokens are separate from PyPI tokens, and old username/password authentication has been deprecated. Check the `[pypitest]` section of `~/.pypirc` uses `username = __token__` with a TestPyPI-issued token in the `password` field.
