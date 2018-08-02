#!/usr/bin/env python

import pmagpy.pmag as pmag

def main():
    """
    Take out dos problem characters from any file
    """
    filename = pmag.get_named_arg('-f')
    if not filename:
        return
    with open(filename, 'rb+') as f:
        content = f.read()
        f.seek(0)
        f.write(content.replace(b'\r', b''))
        f.truncate()

if __name__ == "__main__":
    main()
