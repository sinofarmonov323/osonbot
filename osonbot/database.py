import sqlite3


class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self._table_name = None
    
    def _map_type(self, py_type: type) -> str:
        type_map = {
            int: "INTEGER",
            str: "TEXT",
            float: "REAL",
            bool: "INTEGER",
            bytes: "BLOB"
        }
        return type_map.get(py_type, "TEXT")

    def _table_exists(self, table_name: str) -> bool:
        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
            return cur.fetchone() is not None

    def _get_existing_columns(self, table_name: str) -> set[str]:
        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table_name});")
            return {row[1] for row in cur.fetchall()}  # row[1] is column name

    def create_default_table(self, table_name: str, **columns: type):
        """
        Create the table if not exists. If it exists, add any missing columns.
        Passing columns overwrites defaults (i.e. you supply exact columns you want).
        """

        if not columns:
            # If you want defaults when user omitted columns, uncomment:
            # columns = {"username": str, "user_id": int}
            raise ValueError("You must provide at least one column.")

        self._table_name = table_name  # remember last created (or used) table

        # Build column definitions for CREATE TABLE
        cols = []
        for name, py_type in columns.items():
            sqlite_type = self._map_type(py_type)
            cols.append(f"{name} {sqlite_type} UNIQUE")

        columns_def = ", ".join(cols)
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def});"

        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute(create_sql)

        # If table already existed, make sure missing columns are added
        if self._table_exists(table_name):
            existing = self._get_existing_columns(table_name)
            # For each requested column not present, add it
            for name, py_type in columns.items():
                if name not in existing:
                    col_type = self._map_type(py_type)
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {name} {col_type};"
                    with sqlite3.connect(self.db_name) as conn:
                        conn.execute(alter_sql)
    
    def overwrite_table(self, table_name: str, **columns: type):
        """
        Drops the table (if exists) and creates it with the given columns.
        WARNING: This destroys existing data in that table.
        """
        if not columns:
            raise ValueError("You must provide at least one column.")
        drop_sql = f"DROP TABLE IF EXISTS {table_name};"
        cols = []
        for name, py_type in columns.items():
            sqlite_type = self._map_type(py_type)
            cols.append(f"{name} {sqlite_type} UNIQUE")
        create_sql = f"CREATE TABLE {table_name} ({', '.join(cols)});"
        with sqlite3.connect(self.db_name) as conn:
            conn.execute(drop_sql)
            conn.execute(create_sql)
        self._table_name = table_name

    def add_data(self, table_name, **data):
        if not data:
            raise ValueError("You must provide at least one column and value.")

        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        values = tuple(data.values())

        query = f"INSERT OR IGNORE INTO {table_name} ({columns}) VALUES ({placeholders});"

        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute(query, values)
    
    def get_data(self, table_name: str):
        with sqlite3.connect(self.db_name) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            return [dict(row) for row in cur.execute(f"SELECT * FROM {table_name}").fetchall()]
    
    def create_table(self, table_name: str, **columns: type):
        """
        Create the table if not exists. If it exists, add any missing columns.
        Passing columns overwrites defaults (i.e. you supply exact columns you want).
        """

        if not columns:
            # If you want defaults when user omitted columns, uncomment:
            # columns = {"username": str, "user_id": int}
            raise ValueError("You must provide at least one column.")

        self._table_name = table_name  # remember last created (or used) table

        # Build column definitions for CREATE TABLE
        cols = []
        for name, py_type in columns.items():
            sqlite_type = self._map_type(py_type)
            cols.append(f"{name} {sqlite_type} UNIQUE")

        columns_def = ", ".join(cols)
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def});"

        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute(create_sql)

        # If table already existed, make sure missing columns are added
        if self._table_exists(table_name):
            existing = self._get_existing_columns(table_name)
            # For each requested column not present, add it
            for name, py_type in columns.items():
                if name not in existing:
                    col_type = self._map_type(py_type)
                    alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {name} {col_type};"
                    with sqlite3.connect(self.db_name) as conn:
                        conn.execute(alter_sql)