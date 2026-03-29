import os
import sys
from pathlib import Path


base_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
tcl_dir = base_dir / "tcl"
tcl_library = tcl_dir / "tcl8.6"
tk_library = tcl_dir / "tk8.6"

if tcl_library.is_dir():
    os.environ["TCL_LIBRARY"] = str(tcl_library)

if tk_library.is_dir():
    os.environ["TK_LIBRARY"] = str(tk_library)
