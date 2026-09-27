from __future__ import annotations

import argparse
from pprint import pprint
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from storefront_mail_service import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Register storefront lifecycle templates")
    parser.add_argument("--store-name", required=True)
    parser.add_argument("--namespace", required=True)
    args = parser.parse_args()

    client = TestClient(app)
    response = client.post(
        "/templates/register",
        json={"store_name": args.store_name, "namespace": args.namespace},
    )
    response.raise_for_status()
    pprint(response.json())


if __name__ == "__main__":
    main()
