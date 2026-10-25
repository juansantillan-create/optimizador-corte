"""`python -m optimizador ...`: la línea de comandos (se completa en la fase F1)."""

import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:
    print(f"optimizador-corte {__version__}: todavía no hay motor (fase F0).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
