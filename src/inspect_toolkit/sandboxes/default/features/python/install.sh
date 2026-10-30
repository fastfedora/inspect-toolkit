#!/usr/bin/env bash
set -euo pipefail

/opt/scripts/install-python.sh

# Install Python packages commonly used for development.
# pytest is capped below 9.2: pytest 9.2 removed the private `_pytest.warnings.apply_warning_filters`
# that pytest-isolate 0.0.17 (its latest release) still calls, so the `--isolate` plugin below
# crashes on every test under pytest >= 9.2. pytest-isolate declares no pytest upper bound, so pip
# would otherwise pull an incompatible pytest. Lift this once pytest-isolate supports pytest 9.2.
pip3 install \
    "pytest<9.2" \
    pytest-cov \
    pylint

# Ensure tests can be run in isolated sub-processes with timeouts
pip3 install pytest-isolate
