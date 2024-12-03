import sqlite3
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_file="run_detections.db"):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE NOT NULL,
            date_time DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS Detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            x_coordinate REAL NOT NULL,
            y_coordinate REAL NOT NULL,
            class INTEGER NOT NULL,
            FOREIGN KEY (run_id) REFERENCES Runs(run_id)
        );
        ''')
        self.conn.commit()

    def create_new_run(self):
        # Generate a unique run_id
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.cursor.execute("INSERT INTO Runs (run_id) VALUES (?)", (run_id,))
        self.conn.commit()
        return run_id

    def insert_run(self, run_id):
        self.cursor.execute("INSERT INTO Runs (run_id) VALUES (?)", (run_id,))
        self.conn.commit()

    def insert_detection(self, run_id, x, y, cls, image=None):
        self.cursor.execute(
            "INSERT INTO Detections (run_id, x_coordinate, y_coordinate, class, image) VALUES (?, ?, ?, ?, ?)",
            (run_id, x, y, cls, image)
        )
        self.conn.commit()

    def close_db(self):
        # Close the database connection
        self.conn.close()
