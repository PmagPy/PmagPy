#!/usr/bin/env python
"""Retired MagIC Data Model 2 anisotropy command."""

import sys


def main():
    message = (
        "aniso_magic2.py is retired and will be removed in a future release. "
        "Convert MagIC Data Model 2 files to Data Model 3 and use aniso_magic.py."
    )
    if "-h" in sys.argv:
        print(message)
        return
    raise SystemExit(message)


if __name__ == "__main__":
    main()
