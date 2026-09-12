import argparse
import json
from pathlib import Path

from backend.config import Settings
from backend.main import create_app


def export():
    settings = Settings(
        mysql_password="contract-only", jwt_secret="contract-only-secret-with-at-least-32-characters"
    )
    return json.dumps(create_app(settings).openapi(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = Path(__file__).parents[1] / "openapi" / "openapi.json"
    content = export()
    if args.check:
        if path.read_text(encoding="utf-8") != content:
            raise SystemExit("OpenAPI desatualizado; execute python -m backend.export_openapi")
    else:
        path.write_text(content, encoding="utf-8")
