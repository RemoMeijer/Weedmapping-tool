import json
import sqlite3
from datetime import datetime
import os

class DatabaseHandler:
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        database_name = os.path.join(script_dir, 'detections.db')
        self.conn = sqlite3.connect(database_name)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()
        self._initialize_db()

    def _initialize_db(self):
        # Create Fields table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
        ''')

        # Create Crops table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Crops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
        ''')

        # Create Runs table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT UNIQUE NOT NULL,
                date_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                field_id INTEGER NOT NULL,
                crop_id INTEGER NOT NULL,
                FOREIGN KEY (field_id) REFERENCES Fields(id) ON DELETE CASCADE,
                FOREIGN KEY (crop_id) REFERENCES Crops(id)
);
        ''')

        # Create Detections table
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
        return run_id

    def add_field(self, name):
        """Add a new field to the Fields table."""
        try:
            self.cursor.execute('INSERT INTO Fields (name) VALUES (?)', (name,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"Field '{name}' already exists.")

    def add_crop(self, name):
        """Add a new crop to the Crops table."""
        try:
            self.cursor.execute('INSERT INTO Crops (name) VALUES (?)', (name,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"Crop '{name}' already exists.")

    def ensure_field_exists(self, field_name):
        """Ensure the field exists in the Fields table, adding it if necessary."""
        self.cursor.execute('SELECT id FROM Fields WHERE name = ?', (field_name,))
        if not self.cursor.fetchone():  # Field does not exist
            self.add_field(field_name)

    def ensure_crop_exists(self, crop_name):
        """Ensure the crop exists in the Crops table, adding it if necessary."""
        self.cursor.execute('SELECT id FROM Crops WHERE name = ?', (crop_name,))
        if not self.cursor.fetchone():  # Crop does not exist
            self.add_crop(crop_name)

    def add_run(self, run_id, field_name, crop_name):
        """Add a new run, associating it with a field and a crop."""
        # Ensure field exists and get its ID
        self.ensure_field_exists(field_name)
        self.cursor.execute('SELECT id FROM Fields WHERE name = ?', (field_name,))
        field = self.cursor.fetchone()
        if not field:
            print(f"Field '{field_name}' does not exist.")
            return
        field_id = field[0]

        # Ensure crop exists and get its ID
        self.cursor.execute('SELECT id FROM Crops WHERE name = ?', (crop_name,))
        crop = self.cursor.fetchone()
        if not crop:
            print(f"Crop '{crop_name}' does not exist.")
            return
        crop_id = crop[0]

        try:
            # Use the actual INTEGER IDs for both field and crop
            self.cursor.execute('''
                INSERT INTO Runs (run_id, field_id, crop_id)
                VALUES (?, ?, ?)
            ''', (run_id, field_id, crop_id))
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"Run ID '{run_id}' already exists.")

    def add_detection(self, run_id, x, y, detection_class):
        """Add a new detection for a given run."""
        self.cursor.execute('SELECT run_id FROM Runs WHERE run_id = ?', (run_id,))
        if not self.cursor.fetchone():
            print(f"Run ID '{run_id}' does not exist.")
            return

        self.cursor.execute('''
            INSERT INTO Detections (run_id, x_coordinate, y_coordinate, class)
            VALUES (?, ?, ?, ?)
        ''', (run_id, x, y, detection_class))
        self.conn.commit()

    def get_runs_by_crop(self, crop_name):
        """Get all runs for a specific crop."""
        self.cursor.execute('''
            SELECT r.run_id, r.date_time, f.name AS field_name
            FROM Runs r
            JOIN Crops c ON r.crop_id = c.id
            JOIN Fields f ON r.field_id = f.id
            WHERE c.name = ?
        ''', (crop_name,))
        return self.cursor.fetchall()

    def get_runs_by_field_id(self, field_id):
        """Get all runs for a specific field ID."""
        self.cursor.execute('''
            SELECT r.run_id, r.date_time, c.name AS crop_name
            FROM Runs r
            JOIN Crops c ON r.crop_id = c.id
            WHERE r.field_id = ?
        ''', (field_id,))
        return self.cursor.fetchall()

    def get_field_by_run_id(self, run_id):
        """Get the field name where the given run_id took place."""
        self.cursor.execute('''
                SELECT r.field_id
                FROM Runs r
                WHERE r.run_id = ?
            ''', (run_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]  # Return the field name
        else:
            print(f"No field found for run_id '{run_id}'.")
            return None

    def get_field_id_by_field_name(self, field_name):
        """
        Get the field ID from a field name
        """
        self.cursor.execute('''
            SELECT id FROM Fields 
            WHERE name = ?;
        ''', (field_name,))

        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_field_name_by_field_id(self, field_id):
        """Get field name from its ID"""
        self.cursor.execute('''
            SELECT name FROM Fields 
            WHERE id = ?;
        ''', (field_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_runs_in_timeframe(self, start_date, end_date):
        """Get all runs within a given timeframe."""
        self.cursor.execute('''
            SELECT r.run_id, r.date_time, f.name AS field_name, c.name AS crop_name
            FROM Runs r
            JOIN Fields f ON r.field_id = f.id
            JOIN Crops c ON r.crop_id = c.id
            WHERE r.date_time BETWEEN ? AND ?
        ''', (start_date, end_date))
        return self.cursor.fetchall()

    def get_all_fields(self):
        self.cursor.execute("SELECT name FROM Fields")
        return [row[0] for row in self.cursor.fetchall()]

    def get_all_crops(self):
        self.cursor.execute("SELECT name FROM Crops")
        return [row[0] for row in self.cursor.fetchall()]

    def get_all_runs(self):
        self.cursor.execute("SELECT run_id FROM Runs")
        return [row[0] for row in self.cursor.fetchall()]

    def close_db(self):
        # Close the database connection
        self.conn.close()

    def get_detections_by_run_id(self, run_id):
        """Get all detections for a specific run ID."""
        self.cursor.execute('''
            SELECT x_coordinate, y_coordinate, class
            FROM Detections
            WHERE run_id = ?
        ''', (run_id,))
        return self.cursor.fetchall()

    def delete_run_by_run_id(self, run_id):
        """Delete all detections for a specific run ID."""
        self.cursor.execute('''
        DELETE FROM Detections WHERE run_id = ?
        ''', (run_id,))
        self.cursor.execute('''
        DELETE FROM Runs WHERE run_id = ?
        ''', (run_id,))
        self.conn.commit()

    def delete_all_runs_and_detections(self):
        # Never touch this one lol
        """Delete all rows from Runs and Detections tables."""
        self.cursor.execute('DELETE FROM Detections')
        self.cursor.execute('DELETE FROM Runs')
        self.cursor.execute('DELETE FROM Fields')

        self.conn.commit()

    def import_geojson_data(self, geojson_path):
        """
        Import fields and crops from a GeoJSON file
        Skips geometry data as requested
        """
        with open(geojson_path, 'r') as f:
            geojson_data = json.load(f)

        seen_fields = set()
        seen_crops = set()

        for feature in geojson_data['features']:
            props = feature.get('properties', {})

            # Add field (using ID from properties)
            field_id = props.get('id')
            if field_id and field_id not in seen_fields:
                field_name = f"Field_{field_id}"
                self.add_field(field_name)
                seen_fields.add(field_id)

            # Add crop (using 'gewas' from properties)
            crop_name = props.get('gewas')
            if crop_name and crop_name not in seen_crops:
                self.add_crop(crop_name.strip())  # Clean up whitespace
                seen_crops.add(crop_name)

        print(f"Imported {len(seen_fields)} fields and {len(seen_crops)} crops")
