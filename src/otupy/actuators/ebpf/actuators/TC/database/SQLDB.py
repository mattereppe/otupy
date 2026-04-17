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
                    section TEXT,
                    interface TEXT,
                    UNIQUE(uid, file_path, file_name, attach_type, direction, section, interface)
                )
            """
            )

            conn.commit()
    def add_hookpoint(self, uid, file_path, file_name, calculated_hash, attach_type, direction, Section, interface):
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
                INSERT INTO hooks (uid, file_path, file_name, calculated_hash, attach_type, direction, section, interface)
                VALUES (?, ?, ?, ?, ?, ?, ?,?)
                """,
                (uid, file_path, file_name, calculated_hash, attach_type, direction, Section, interface)
            )
            conn.commit()
    def exists_file(self, uid, file_path=None, file_name=None, attach_type=None, direction=None, Section=None, interface=None) -> bool :
        """
        Retrieves hookpoints for a given UID and optional filters.

        Args:
            uid (str): User identifier.
            file_path (str, optional): Filter by file path.
            file_name (str, optional): Filter by file name.
            attach_type (str, optional): Filter by attach type.
            direction (str, optional): Filter by direction.
            Section (str, optional): Filter by section.
            iface (str, optional): Filter by interface.

        Returns:
            bool: True if a matching record exists, False otherwise.

        """
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            query = "SELECT 1 FROM hooks WHERE uid = ?"
            params = [uid]

            if file_path:
                query += " AND file_path = ?"
                params.append(file_path)
            if file_name:
                query += " AND file_name = ?"
                params.append(file_name)
            if attach_type:
                query += " AND attach_type = ?"
                params.append(attach_type)
            if direction:
                query += " AND direction = ?"
                params.append(direction)
            if Section:
                query += " AND section = ?"
                params.append(Section)
            if interface:
                query += " AND interface = ?"
                params.append(interface)

            c.execute(query, tuple(params))
            return c.fetchone() is not None
    def delete_hookpoint(self, uid, file_path=None, file_name=None, attach_type=None, direction=None, Section=None, interface=None):
        """
        Deletes hookpoints for a given UID and optional filters.

        Args:
            uid (str): User identifier.
            file_path (str, optional): Filter by file path.
            file_name (str, optional): Filter by file name.
            attach_type (str, optional): Filter by attach type.
            direction (str, optional): Filter by direction.
            Section (str, optional): Filter by section.
            iface (str, optional): Filter by interface.

        """
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            query = "DELETE FROM hooks WHERE uid = ?"
            params = [uid]

            if file_path:
                query += " AND file_path = ?"
                params.append(file_path)
            if file_name:
                query += " AND file_name = ?"
                params.append(file_name)
            if attach_type:
                query += " AND attach_type = ?"
                params.append(attach_type)
            if direction:
                query += " AND direction = ?"
                params.append(direction)
            if Section:
                query += " AND section = ?"
                params.append(Section)
            if interface:
                query += " AND interface = ?"
                params.append(interface)

            c.execute(query, tuple(params))
            conn.commit()
    def retrieve_hookpoints(self, uid, file_path=None, file_name=None, attach_type=None, direction=None, Section=None, interface=None) -> list:
        """
        Retrieves hookpoints for a given UID and optional filters.

        Args:
            uid (str): User identifier.
            file_path (str, optional): Filter by file path.
            file_name (str, optional): Filter by file name.
            attach_type (str, optional): Filter by attach type.
            direction (str, optional): Filter by direction.
            Section (str, optional): Filter by section.
            iface (str, optional): Filter by interface.

        Returns:
            list: A list of matching hookpoints.

        """
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            query = "SELECT * FROM hooks WHERE uid = ?"
            params = [uid]

            if file_path:
                query += " AND file_path = ?"
                params.append(file_path)
            if file_name:
                query += " AND file_name = ?"
                params.append(file_name)
            if attach_type:
                query += " AND attach_type = ?"
                params.append(attach_type)
            if direction:
                query += " AND direction = ?"
                params.append(direction)
            if Section:
                query += " AND section = ?"
                params.append(Section)
            if interface:
                query += " AND interface = ?"
                params.append(interface)

            c.execute(query, tuple(params))
            return c.fetchall()
db = SQLDatabase()