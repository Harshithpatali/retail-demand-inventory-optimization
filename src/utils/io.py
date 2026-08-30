from pathlib import Path
import pandas as pd


def require_files(root: Path, names: list[str]) -> None:
    missing = [str(root / name) for name in names if not (root / name).exists()]
    if missing:
        raise FileNotFoundError("Missing required file(s):\n" + "\n".join(missing))


def read_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing prerequisite: {path}")
    return pd.read_parquet(path)


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
