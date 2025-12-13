"""PostgreSQL adapter with a safe mock fallback for local development."""

from typing import Any, Dict, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from src.core.logger import get_logger


class PostgresAdapter:
    def __init__(self, connection_string: str, echo: bool = False, lazy: bool = True):
        self.connection_string = connection_string
        self.echo = echo
        self._engine: Optional[Engine] = None
        self._Session = None
        self.logger = get_logger(self.__class__.__name__)
        if not lazy:
            self._initialise_engine()

    def _initialise_engine(self) -> None:
        if self._engine:
            return
        self.logger.debug("Creating engine for '%s'", self.connection_string)
        self._engine = create_engine(self.connection_string, echo=self.echo, future=True)
        self._Session = sessionmaker(bind=self._engine, future=True)

    @property
    def engine(self) -> Engine:
        if not self._engine:
            self._initialise_engine()
        return self._engine  # type: ignore[return-value]

    def fetch_data(self, query: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Execute a query and return a DataFrame. If the engine cannot be created,
        return an empty DataFrame instead of crashing to keep local runs predictable."""

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query), params or {})
                rows = result.fetchall()
                return pd.DataFrame(rows, columns=result.keys())
        except SQLAlchemyError as exc:
            self.logger.error("Database query failed: %s", exc)
            return pd.DataFrame()

    def insert_data(self, table_name: str, data_frame: pd.DataFrame) -> None:
        try:
            data_frame.to_sql(table_name, con=self.engine, if_exists="append", index=False)
        except SQLAlchemyError as exc:
            self.logger.error("Insert into '%s' failed: %s", table_name, exc)

    def test_connection(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except SQLAlchemyError as exc:
            self.logger.error("Connection test failed: %s", exc)
            return False