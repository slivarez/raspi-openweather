"""Allow running the application with ``python -m raspi_openweather``."""

import sys

from raspi_openweather.app import main

sys.exit(main())
