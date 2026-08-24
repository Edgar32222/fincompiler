from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    try:
        from streamlit.web import cli as streamlit_cli
    except ImportError as exc:
        raise RuntimeError("The web UI requires: pip install 'fincompiler[web]'") from exc
    app = Path(__file__).with_name("streamlit_entry.py")
    extra_arguments = sys.argv[1:]
    sys.argv = ["streamlit", "run", str(app), *extra_arguments]
    return int(streamlit_cli.main() or 0)


if __name__ == "__main__":
    raise SystemExit(main())
