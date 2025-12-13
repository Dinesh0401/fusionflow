"""Data warehouse adapter with a lightweight in-memory sink."""

from typing import Any, List, Optional

import pandas as pd

from src.core.logger import get_logger


class WarehouseAdapter:
    def __init__(self, connection_string: str = "warehouse://local/mock"):
        self.connection_string = connection_string
        self.connection = None
        self._loaded_tables: dict = {}
        self.logger = get_logger(self.__class__.__name__)

    def connect(self) -> None:
        # In a production adapter, establish and cache the connection here.
        self.logger.debug("Connecting to warehouse '%s'", self.connection_string)
        self.connection = True

    def load_data(self, data_frame: pd.DataFrame, table_name: str) -> None:
        if data_frame is None:
            raise ValueError("No data provided for loading.")
        if self.connection is None:
            self.connect()

        # Store data in-memory for now; production implementation would write to the warehouse.
        self._loaded_tables[table_name] = data_frame
        self.logger.info("Loaded %s rows into table '%s'", len(data_frame), table_name)

    def get_table(self, table_name: str) -> Optional[pd.DataFrame]:
        return self._loaded_tables.get(table_name)

    def close_connection(self) -> None:
        self.connection = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()