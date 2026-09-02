"""
pmagpy-convert: the converter registry on the command line.

The same source the hub's Convert page is generated from
(:mod:`pmagpy.convert_registry`) drives one command for every format, so a
conversion typed in a shell, run from a script and clicked in the app are the
same call with the same names::

    pmagpy-convert                                  # the formats
    pmagpy-convert sio --help                       # what SIO asks for
    pmagpy-convert sio af.dat thermal.dat --codelist AF T --location Hawaii --dir ~/MagIC/Hawaii
    pmagpy-convert tdt --dir ~/MagIC/ATPI            # a directory format reads --dir itself
    pmagpy-convert cit PI47-.sam --samp-con 2 --specnum 1 --append

Options are the registry's fields with dashes for underscores; a ``bool`` field
that defaults on is turned off with ``--no-<name>``. The tables go to ``--dir``
(the working directory when not given), replacing what is there unless
``--append`` is passed, and the conversion is added to the directory's
``pmagpy_conversions.json`` unless ``--no-record`` is. The older
``programs/conversion_scripts`` keep their own flags; this command does not
replace them.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional, Sequence

from pmagpy import convert_registry as reg

PROG = "pmagpy-convert"


def option_name(field: reg.Field) -> str:
    """``--samp-con`` for the field ``samp_con``; ``--no-noave`` for a bool that defaults on."""
    flag = field.name.replace("_", "-")
    if field.kind == "bool" and field.default:
        return f"--no-{flag}"
    return f"--{flag}"


def format_help(fmt: reg.Format) -> str:
    """The description under the usage line: the format, its notes, its example files."""
    function = fmt.function
    where = repr(function) if isinstance(function, reg.Deferred) else f"{function.__module__}.{function.__name__}"
    lines = [f"{fmt.label} — {where}"]
    if fmt.notes:
        lines.append(fmt.notes)
    if fmt.takes_directory:
        lines.append("Reads the whole directory given by --dir; no files are named.")
    elif fmt.extensions:
        lines.append(f"Files usually end in {', '.join(fmt.extensions)}.")
    if fmt.needs:
        lines.append(f"Needs {', '.join(t + '.txt' for t in fmt.needs)} in --dir first.")
    if fmt.examples:
        rel, values = fmt.examples[0]
        words = []
        for f in fmt.fields:
            if f.name not in values:
                continue
            if f.kind == "bool":
                if bool(values[f.name]) != bool(f.default):
                    words.append(option_name(f))
            else:
                words.append(f"{option_name(f)} {_shell(values[f.name])}")
        lines.append(f"Example: {PROG} {fmt.key} {'' if fmt.takes_directory else os.path.basename(rel) + ' '}{' '.join(words)}".rstrip())
    return "\n".join(lines)


def _shell(value) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(v) for v in value)
    text = str(value)
    return f'"{text}"' if " " in text else text


def field_help(field: reg.Field) -> str:
    """One line per option: the label, the help, the default, the choices spelled out."""
    parts = [field.label + ("." if not field.label.endswith(".") else "")]
    if field.help:
        parts.append(field.help)
    if field.kind == "naming":
        parts.append("Codes: " + "; ".join(f"{code} = {text}" for code, text in reg.NAMING_CONVENTIONS) + ".")
    elif field.kind in ("choice", "codes") and field.choices:
        parts.append("Choices: " + "; ".join(f"{v} = {label}" if label and label != v else str(v)
                                             for v, label in field.choices if str(v) != "") + ".")
    if field.kind == "bool":
        parts.append("On unless this is given." if field.default else "Off unless this is given.")
    elif field.default not in (None, "", [], ()):
        parts.append(f"Default {field.default}.")
    if field.required:
        parts.append("Required.")
    return " ".join(str(p) for p in parts).replace("%", "%%")


def add_field(parser: argparse.ArgumentParser, field: reg.Field) -> None:
    """One ``argparse`` option for one registry field."""
    name = option_name(field)
    kwargs: dict = {"dest": field.name, "help": field_help(field), "default": argparse.SUPPRESS}
    if field.kind == "bool":
        kwargs["action"] = "store_false" if field.default else "store_true"
    elif field.kind == "int":
        kwargs["type"] = int
        kwargs["metavar"] = "N"
    elif field.kind == "float":
        kwargs["type"] = float
        kwargs["metavar"] = "X"
    elif field.kind == "choice" and field.choices:
        choices = [str(v) for v, _ in field.choices if str(v) != ""]          # the blank choice is "leave it out"
        kwargs["choices"] = choices
        kwargs["type"] = str
        kwargs["metavar"] = "{" + ",".join(choices) + "}"
    elif field.kind == "codes":
        kwargs["nargs"] = "+"
        if field.choices:
            kwargs["choices"] = [str(v) for v, _ in field.choices if str(v) != ""]
        kwargs["metavar"] = "CODE"
    elif field.kind == "naming":
        kwargs["metavar"] = "CODE"
    else:
        kwargs["metavar"] = "TEXT"
    parser.add_argument(name, **kwargs)


def build_parser(fmt: reg.Format) -> argparse.ArgumentParser:
    """The parser for one format: its files, the directory options, then its fields."""
    parser = argparse.ArgumentParser(prog=f"{PROG} {fmt.key}", description=format_help(fmt),
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    if not fmt.takes_directory:
        parser.add_argument("files", nargs="+", metavar="FILE", help="the instrument files to convert")
    where = parser.add_argument_group("where")
    where.add_argument("--dir", dest="dir_path", default=".", metavar="DIR",
                       help="the MagIC directory the tables are written to (and, for a directory format, read from). "
                            "A FILE not found from the working directory is looked for there. Default: the working directory.")
    where.add_argument("--append", action="store_true", help="add to the tables already in DIR instead of replacing them")
    where.add_argument("--no-record", dest="record", action="store_false",
                       help=f"do not add this conversion to DIR's {reg.CONVERSION_LOG}")
    where.add_argument("--log", action="store_true", help="print everything the converter printed")
    fields = parser.add_argument_group(f"what {fmt.label} asks")
    for field in fmt.fields:
        add_field(fields, field)
    return parser


def field_values(fmt: reg.Format, namespace: argparse.Namespace) -> dict:
    """Canonical field name → value for the fields that were given on the command line."""
    return {f.name: getattr(namespace, f.name) for f in fmt.fields if hasattr(namespace, f.name)}


def list_formats() -> str:
    """One line per format: key, label, what its files look like."""
    width = max(len(k) for k in reg.FORMATS)
    lines = [f"{PROG} FORMAT [FILE ...] [options]    -- {PROG} FORMAT --help for a format's options", ""]
    for key, fmt in sorted(reg.FORMATS.items()):
        looks = ("a directory" if fmt.takes_directory else ", ".join(fmt.extensions) or "files")
        lines.append(f"  {key:<{width}}  {fmt.label} ({looks})")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None, out=None) -> int:
    """Entry point. Returns the exit status: 0 converted, 1 the conversion failed, 2 bad usage."""
    out = out or sys.stdout
    args: List[str] = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help"):
        print(list_formats(), file=out)
        return 0
    key = args[0]
    if key not in reg.FORMATS:
        close = [k for k in reg.FORMATS if key.lower() in k or k in key.lower()]
        print(f"{PROG}: no format called '{key}'." + (f" Did you mean {', '.join(close)}?" if close else ""), file=out)
        print(list_formats(), file=out)
        return 2
    fmt = reg.FORMATS[key]
    parser = build_parser(fmt)
    namespace = parser.parse_args(args[1:])
    dir_path = os.path.abspath(os.path.expanduser(namespace.dir_path))
    inputs = [dir_path] if fmt.takes_directory else [os.path.abspath(f) if os.path.exists(f) else f for f in namespace.files]
    values = field_values(fmt, namespace)
    missing = [f.label for f in fmt.fields if f.required and f.name not in values]
    if missing:
        parser.error(f"{fmt.label} needs {', '.join(missing)}")
    try:
        result = reg.convert_files(fmt, inputs, values, dir_path, append=namespace.append, record=namespace.record,
                                   report=lambda text: print(text, file=out))
    except ValueError as err:                    # a naming code without its count, and the like
        parser.error(str(err))
    if namespace.log and result.log.strip():
        print(result.log.rstrip(), file=out)
    print(result.message, file=out)
    for name, why in result.failed:
        print(f"  {name}: {why}", file=out)
    if result.ok:
        print(f"Tables written to {dir_path}", file=out)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
