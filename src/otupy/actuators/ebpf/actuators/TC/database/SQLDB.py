import sqlite3


class SQLDatabase:
    """
    A simple SQLite database class to manage copied artifacts and process IDs (PIDs).
    """

    def __init__(self, db_name="kerneldata.db"):
        """
        Initializes the database and ensures required tables exist.

        Args:
            db_name (str): The name of the SQLite database file. Default is 'kerneldata.db'.
        """
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """
        Initializes the database by creating necessary tables if they do not exist.
        """
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()

            
            c.execute(
                """
                CREATE TABLE IF NOT EXISTS hooks (
                    uid TEXT,
                    file_path TEXT,
                    file_name TEXT,
                    calculated_hash TEXT,
                    attach_type TEXT,
                    direction TEXT,
                    Section TEXT,
                    UNIQUE(uid, file_path, file_name)
                )
            """
            )

            conn.commit()
    def add_hookpoint(self, uid, file_path, file_name, calculated_hash, attach_type, direction, Section):
        """
        Inserts a file record for a given UID, file path, file name, and hash. Throws an error if the file already exists.

        Args:
            uid (str): User identifier.
            file_path (str): The path where the file is stored.
            file_name (str): The name of the file.
            calculated_hash (str): The MD5 hash of the file.
            attach_type (str): The attach type of the eBPF program.
            direction (str): The direction of the eBPF program.
            Section (str): The section of the eBPF program.
        """
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO hooks (uid, file_path, file_name, calculated_hash, attach_type, direction, Section)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (uid, file_path, file_name, calculated_hash, attach_type, direction, Section),
            )
            conn.commit()

db = SQLDatabase()