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
    return pytest.main(["tests/test_auth.py", "tests/test_health.py", "tests/test_documents.py", "-q"])


if __name__ == "__main__":
    raise SystemExit(main())
