"""Data transformation utilities."""

from typing import Iterable, List, Mapping, MutableMapping

import pandas as pd


class DataTransformer:
    def clean_data(self, data):
        """Perform light cleaning.

        - For pandas DataFrames: drop duplicate rows and trim string columns.
        - For iterables of mappings: normalize keys and remove None values.
        """

        if isinstance(data, pd.DataFrame):
            cleaned = data.drop_duplicates().copy()
            for col in cleaned.select_dtypes(include=["object", "string"]):
                cleaned[col] = cleaned[col].astype(str).str.strip()
            return cleaned

        if isinstance(data, Iterable):
            cleaned_rows: List[MutableMapping] = []
            for row in data:
                if isinstance(row, Mapping):
                    cleaned_row = {str(k).strip(): v for k, v in row.items() if v is not None}
                    cleaned_rows.append(cleaned_row)
            return cleaned_rows

        return data

    def enrich_data(self, data):
        """Attach derived fields; this is intentionally minimal for the sample pipeline."""

        if isinstance(data, pd.DataFrame):
            data = data.copy()
            data["row_number"] = range(1, len(data) + 1)
            return data

        if isinstance(data, list):
            enriched: List[MutableMapping] = []
            for idx, row in enumerate(data, start=1):
                if isinstance(row, MutableMapping):
                    enriched_row = dict(row)
                    enriched_row["row_number"] = idx
                    enriched.append(enriched_row)
            return enriched

        return data

    def transform(self, data):
        cleaned_data = self.clean_data(data)
        return self.enrich_data(cleaned_data)