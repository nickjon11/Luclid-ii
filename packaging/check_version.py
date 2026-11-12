"""Ensure the source and installer share a single version before publishing."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
version = (root / 'VERSION').read_text(encoding="utf-8").strip()
assert re.fullmatch(r'\d+\.\d+\.\d+', version), version
app = (root / 'src/local_muse/version.py').read_text(encoding="utf-8")
project = (root / 'pyproject.toml').read_text(encoding="utf-8")
setup = (root / 'Luclid-ii-Setup.py').read_text(encoding="utf-8")
assert re.search(rf"APP_VERSION\s*=\s*['\"]{re.escape(version)}['\"]", app)
assert f'version = "{version}"' in project
assert 'APP_VERSION = release_version()' in setup
assert 'v0.6.24' not in setup
assert 'write_text(APP_VERSION)' in setup
print(f'Version check passed: {version}')
