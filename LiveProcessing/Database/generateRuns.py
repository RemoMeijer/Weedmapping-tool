import sqlite3
import uuid
import random
import math

# --- Field Coordinates (Corners in order: A, B, C, D) ---
# A: Bottom-left, B: Bottom-right, C: Top-right, D: Top-left
A = (51.465984, 3.628045)
B = (51.466209, 3.629848)
C = (51.468370, 3.628040)
D = (51.467745, 3.626391)

# --- Parameters ---
field_id = 19
crop_id = 6
row_spacing_m = 1  # in meters
col_spacing_m = 1  # in meters

# --- Approximate conversion: meters to degrees ---
lat_to_deg = 1 / 111111
avg_lat = (A[0] + C[0]) / 2
lon_to_deg = 1 / (111111 * abs(math.cos(math.radians(avg_lat))))

# --- Grid Size ---
# Rough estimation of vertical and horizontal distance for row/col counts
est_height = abs(C[0] - A[0]) / lat_to_deg
est_width = abs(B[1] - A[1]) / lon_to_deg
num_rows = int(est_height / row_spacing_m)
num_cols = int(est_width / col_spacing_m)

# --- Bilinear Interpolation Function ---
def bilinear_interpolation(row_frac, col_frac):
    lat = (
        A[0] * (1 - row_frac) * (1 - col_frac) +
        B[0] * (1 - row_frac) * col_frac +
        C[0] * row_frac * col_frac +
        D[0] * row_frac * (1 - col_frac)
    )
    lon = (
        A[1] * (1 - row_frac) * (1 - col_frac) +
        B[1] * (1 - row_frac) * col_frac +
        C[1] * row_frac * col_frac +
        D[1] * row_frac * (1 - col_frac)
    )
    return (lat, lon)

# --- Create Unique Run ID ---
run_string = str(uuid.uuid4())

# --- Database Connection ---
conn = sqlite3.connect('detections.db')
cursor = conn.cursor()

# Insert new run
cursor.execute(
    "INSERT INTO Runs (run_id, field_id, crop_id) VALUES (?, ?, ?)",
    (run_string, field_id, crop_id)
)

# --- Generate Detections ---
detections = []

for row in range(num_rows):
    for col in range(num_cols):
        row_frac = row / (num_rows - 1) if num_rows > 1 else 0
        col_frac = col / (num_cols - 1) if num_cols > 1 else 0

        lat, lon = bilinear_interpolation(row_frac, col_frac)

        # Weed probability increases across horizontal axis
        weed_prob = min(0.3, max(0.0, col_frac * 0.3))
        class_id = 1 if random.random() < weed_prob else 0

        detections.append((run_string, lat, lon, class_id))

# --- Store Detections ---
cursor.executemany(
    "INSERT INTO Detections (run_id, x_coordinate, y_coordinate, class) VALUES (?, ?, ?, ?)",
    detections
)

conn.commit()
conn.close()

print(f"Inserted {len(detections)} detections into run {run_string}")
