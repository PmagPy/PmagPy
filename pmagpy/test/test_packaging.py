import pathlib
import re


def test_cli_package_requires_matching_pmagpy_version():
    repo_root = pathlib.Path(__file__).resolve().parents[2]

    setup_text = (repo_root / 'command_line_setup.py').read_text(encoding='utf-8')
    version_text = (repo_root / 'pmagpy' / 'version.py').read_text(encoding='utf-8')

    version_value = re.search(r"version\s*=\s*['\"](pmagpy-[^'\"]+)['\"]", version_text)
    assert version_value is not None, 'Could not determine shared version string'

    version_num = version_value.group(1).removeprefix('pmagpy-')
    assert f"shared_version_requirement = f'pmagpy=={{version_num}}'" in setup_text, (
        'pmagpy-cli should build an exact pmagpy version pin from the shared version string'
    )
    assert "shared_version_requirement," in setup_text, (
        'pmagpy-cli should include the computed pmagpy version pin in install_requires'
    )
    assert f"pmagpy=={version_num}" in setup_text, (
        'pmagpy-cli should require the same version of pmagpy as the shared version string'
    )
