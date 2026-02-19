import sys
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent


def run():
    standalone = None
    try:
        import maya.standalone  # type: ignore

        try:
            maya.standalone.initialize(name="python")
            standalone = maya.standalone
        except Exception:
            standalone = None
    except Exception:
        standalone = None

    if TESTS_DIR.as_posix() not in sys.path:
        sys.path.insert(0, TESTS_DIR.as_posix())

    try:
        suite = unittest.defaultTestLoader.discover(
            start_dir=TESTS_DIR.as_posix(),
            pattern="test_layout_procedures_maya.py",
        )
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return result
    finally:
        if standalone is not None:
            try:
                standalone.uninitialize()
            except Exception:
                pass


if __name__ == "__main__":
    test_result = run()
    raise SystemExit(0 if test_result.wasSuccessful() else 1)
