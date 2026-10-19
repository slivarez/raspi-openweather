#!/usr/bin/env python3
# raspi openweather by Granpino. May 2020
# Modified by Alexander Didenko in 2025:
#   - Make it actually work with Python 3.11+
#   - Switch from paid API to free API
#   - Remove data not available in free API
#   - Everything re-adjusted to 800x480 resolution
#   - Day/Night time change of background
"""Backwards compatible launcher, see raspi_openweather.app for the code."""

import sys

from raspi_openweather.app import main

if __name__ == "__main__":
    sys.exit(main())
