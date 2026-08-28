#### Pyinstaller:

For install instructions, see [the setup_scripts README](https://github.com/PmagPy/PmagPy/blob/master/setup_scripts/README.md).

The previous shared `pmag_gui.spec` has been removed because the maintained spec is now Apple-silicon-specific. A dedicated Linux spec must be created and validated before building another Linux standalone; do not use `pmag_gui_macos_arm64.spec` on Linux.
