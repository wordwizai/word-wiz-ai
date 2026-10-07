"""
Index eng_to_ipa's CMU dictionary by word.

eng_to_ipa ships ``resources/CMU_dict.db``, a sqlite table of about 134,000
pronunciations with no index on ``word``. Every lookup (``convert``,
``ipa_list``, ``isin_cmu``) runs ``SELECT ... WHERE word IN (...)``, which
scans the whole table. Word scoring v2 looks up the pronunciation variants of
a sentence's uncached words in one batched query per sentence, which takes
about 15 ms without the index and about 0.3 ms with it, on the request path.

``ensure_index()`` adds the index. It only makes lookups faster: the rows, and
so every transcription, stay exactly the same. The Docker image runs it once
at build time (``RUN python -m core.cmu_index``), and a local venv can run the
same command once. It is never called while serving requests, because it
writes to a file inside the installed package.
"""

from __future__ import annotations

import os
import sqlite3

INDEX_NAME = "idx_dictionary_word"

_CREATE_INDEX = f"CREATE INDEX IF NOT EXISTS {INDEX_NAME} ON dictionary(word)"


def cmu_db_path() -> str | None:
    """Path of eng_to_ipa's ``resources/CMU_dict.db``, or None without the package."""
    try:
        import eng_to_ipa
    except Exception:
        return None
    return os.path.join(
        os.path.dirname(os.path.abspath(eng_to_ipa.__file__)), "resources", "CMU_dict.db",
    )


def ensure_index(db_path: str | None = None) -> bool:
    """
    Create the ``word`` index on the CMU dictionary if it is missing.

    Idempotent. Returns True when the index exists afterwards, and False on
    any failure (no package, missing file, not a database, read-only file)
    without raising.

    Args:
        db_path: the database to index. Defaults to eng_to_ipa's own copy.
    """
    try:
        path = db_path or cmu_db_path()
        # sqlite3.connect would create an empty database at a missing path.
        if not path or not os.path.isfile(path):
            return False
        con = sqlite3.connect(path)
        try:
            con.execute(_CREATE_INDEX)
            con.commit()
        finally:
            con.close()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    _path = cmu_db_path()
    if ensure_index(_path):
        print(f"[OK] CMU dictionary indexed by word ({INDEX_NAME}): {_path}")
    else:
        # Not fatal: lookups still work, they are just slower.
        print(f"[WARN] could not index the CMU dictionary; lookups stay slow: {_path}")
