"""Executa o aceite local carregando .env sem exibir configurações."""
import os
from pathlib import Path
import sys

from dotenv import load_dotenv


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    os.chdir(root)
    load_dotenv(root / ".env", override=False)
    import pytest
    targets = sys.argv[1:] or ["tests/test_auth.py", "tests/test_health.py", "tests/test_documents.py", "tests/test_prototype.py", "tests/test_review03.py", "tests/test_delete_documents.py"]
    return pytest.main([*targets, "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
