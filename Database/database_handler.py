import sqlite3

class DatabaseHandler:
    def __init__(self, db_file="detections.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        """Create the detections table if it doesn't exist."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                center_x REAL,
                center_y REAL,
                class_label INTEGER
            )
        ''')
        self.conn.commit()

    def insert_detection(self, center_x, center_y, class_label):
        """Insert a new detection into the database."""
        self.cursor.execute('''
            INSERT INTO detections (center_x, center_y, class_label)
            VALUES (?, ?, ?)
        ''', (center_x, center_y, class_label))
        self.conn.commit()

    def get_all_detections(self):
        """Retrieve all detections from the database."""
        self.cursor.execute("SELECT * FROM detections")
        return self.cursor.fetchall()

    def close_db(self):
        """Close the database connection."""
        self.conn.close()
