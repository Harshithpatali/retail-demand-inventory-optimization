from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT
    / "data"
    / "processed"
    / "forecast_features.parquet"
)

OUTPUT = (
    ROOT
    / "data"
    / "processed"
    / "series_options.json"
)


def main() -> None:

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Missing: {INPUT}"
        )

    print(
        "Reading only store/item columns..."
    )

    df = pd.read_parquet(
        INPUT,
        columns=[
            "store_id",
            "item_id",
        ],
    )

    pairs = (
        df[
            [
                "store_id",
                "item_id",
            ]
        ]
        .astype(str)
        .drop_duplicates()
        .sort_values(
            [
                "store_id",
                "item_id",
            ]
        )
    )

    options = pairs.to_dict(
        orient="records"
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            {
                "options": options
            },
            f,
            indent=2,
        )

    print(
        f"Created {len(options)} store/item combinations."
    )

    print(
        f"Saved: {OUTPUT}"
    )


if __name__ == "__main__":
    main()