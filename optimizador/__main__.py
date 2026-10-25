"""`python -m optimizador ...`: la línea de comandos (se completa en la fase F1)."""

from __future__ import annotations

import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in ("--version", "version"):
        print(f"optimizador-corte {__version__}")
        return 0
    print(f"optimizador-corte {__version__}: todavía no hay motor (fase F0).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
