"""George Boole Has Entered The Chat — terminal version.

A third sibling to ``web/`` (adenosine, browser) and ``wii/`` (magnolia, C99),
built on the `magmacrunch.engine` terminal backend. The rules are a port of
``wii/source/board.c``; see ``boole/board.py`` for why that source and not the
web one.
"""

# Kept in step with ``pyproject.toml`` by hand, the way ``magmacrunch`` does
# it: a literal answers the same in a source checkout as in an installed
# wheel, which asking importlib.metadata would not. It drifted four releases
# behind — the release workflow compares the git tag against pyproject and
# never looks here, and nothing reads this — so the check now lives in
# ``tests/test_packaging.py``, and bumping one without the other fails there.
__version__ = "0.5.1"
