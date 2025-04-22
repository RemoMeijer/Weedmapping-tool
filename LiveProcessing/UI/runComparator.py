from sklearn.neighbors import KDTree
import numpy as np
from pyproj import Geod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from LiveProcessing.Database.database_handler import DatabaseHandler

"""Compare two runs and make a compared run with comparisons in the database"""
class RunComparator:
    def __init__(self, db: 'DatabaseHandler'):
        self.db = db

    def compare_runs(self, run_id_1, run_id_2, delta_cm=10):
        """
        Compare detections using KDTree for faster nearest neighbor search.

        delta_cm: maximum distance to consider detections as matching (in cm).
        """
        # Convert delta to degrees (~1 deg ≈ 111,000 meters, so 1m ≈ 0.000009 deg)
        # We'll use distance in meters directly in KDTree, so no need to convert to degrees
        max_distance_m = delta_cm / 100

        detections_1 = self.db.get_detections_by_run_id(run_id_1)
        detections_2 = self.db.get_detections_by_run_id(run_id_2)

        field_1 = self.db.get_field_by_run_id(run_id_1)
        field_2 = self.db.get_field_by_run_id(run_id_2)

        if field_1 is None or field_2 is None or field_1 != field_2:
            print("Runs to be compared are not on equal fields!")
            return

        # Convert coordinates to cartesian approximation (in meters)
        geod = Geod(ellps="WGS84")

        # Approximate local projection: treat (lat, lon) as Cartesian for small areas
        def latlon_to_meters(ref_lat, ref_lon, lat, lon):
            _, _, dist = geod.inv(ref_lon, ref_lat, lon, lat)
            # Determine direction
            if lon < ref_lon:
                dist *= -1
            x = dist
            _, _, dist = geod.inv(ref_lon, ref_lat, ref_lon, lat)
            if lat < ref_lat:
                dist *= -1
            y = dist
            return (x, y)

        # Use first detection as reference point
        ref_lat, ref_lon, _ = detections_1[0]

        coords_1 = []
        for det in detections_1:
            x, y = latlon_to_meters(ref_lat, ref_lon, det[0], det[1])
            coords_1.append((x, y))

        coords_2 = []
        for det in detections_2:
            x, y = latlon_to_meters(ref_lat, ref_lon, det[0], det[1])
            coords_2.append((x, y))

        tree = KDTree(coords_2)

        stayed = []
        removed = []
        used_indices = set()

        for i, (coord1, det1) in enumerate(zip(coords_1, detections_1)):
            if i % 100 == 0:
                print(f"[Progress] Compared {i} out of {len(coords_1)} crops...")

            # Query nearest within max_distance_m
            indices = tree.query_radius([coord1], r=max_distance_m, return_distance=False)[0]
            match_found = False
            for j in indices:
                if j in used_indices:
                    continue
                det2 = detections_2[j]
                if det1[2] == det2[2]:
                    stayed.append(det1)
                    used_indices.add(j)
                    match_found = True
                    break
            if not match_found:
                removed.append(det1)

        # todo figure this part out
        new = [det for i, det in enumerate(detections_2) if i not in used_indices]
        # new = []
        differences = {
            'stayed': stayed,
            'removed': removed,
            'new': new,
        }

        self.db.add_compared_run(field_1, run_id_1, run_id_2)
        comparison_id = self.db.get_comparison_run(run_id_1, run_id_2)

        for diff_type, diff_list in differences.items():
            for diff_pair in diff_list:
                if len(diff_pair) != 3:
                    continue
                x, y, _ = diff_pair
                self.db.add_comparison(comparison_id[0], x, y, diff_type)

        return comparison_id
