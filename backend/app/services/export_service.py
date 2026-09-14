from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_dataframe_to_excel(df: pd.DataFrame, output_path: str | Path):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False)
    return str(path)
