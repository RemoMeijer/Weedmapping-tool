from math import sqrt
from pyproj import Geod

from Database.database_handler import DatabaseHandler


class RunComparator:
    def __init__(self, db: 'DatabaseHandler'):
        self.db = db

    def is_similar(self, det1, det2, delta_cm=100):
        # Extract latitude, longitude, and class from detections
        lat1, lon1, class1 = det1
        lat2, lon2, class2 = det2

        # Create a Geod object (WGS84 ellipsoid is commonly used for GPS coordinates)
        geod = Geod(ellps="WGS84")

        # Calculate the geodesic distance between the two points in meters
        _, _, distance_m = geod.inv(lon1, lat1, lon2, lat2)

        # Convert delta from centimeters to meters
        distance_cm = distance_m * 100

        # Check if distance is within delta and classes are the same
        same_type = class1 == class2
        return abs(distance_cm) <= delta_cm and same_type

    def compare_runs(self, run_id_1, run_id_2, delta=0.0002):
        """
        Compares detections between two runs.

        Returns a dictionary with three lists:
            - 'stayed': detections present in both runs
            - 'removed': detections only in run 1 (missing in run 2)
            - 'new': detections only in run 2 (absent in run 1)
        """
        detections_1 = self.db.get_detections_by_run_id(run_id_1)
        detections_2 = self.db.get_detections_by_run_id(run_id_2)

        field_1 = self.db.get_field_by_run_id(run_id_1)
        field_2 = self.db.get_field_by_run_id(run_id_2)
        if field_1 is None or field_2 is None:
            return
        if field_1 != field_2:
            print("Runs to be compared are not on equal fields!")
            return

        # Make copies so we can remove matched items
        detections_2_remaining = detections_2.copy()

        stayed = []
        removed = []

        # For every detection in the first run, try to find a match in the second run
        for det1 in detections_1:
            match_found = False
            for det2 in detections_2_remaining:
                if self.is_similar(det1, det2):
                    # Match if found, so it sadly stayed
                    stayed.append(det1)
                    # Remove the matched detection so it isn’t matched twice
                    detections_2_remaining.remove(det2)
                    match_found = True
                    break

            # No match found, so it's successfully removed.
            if not match_found:
                removed.append(det1)

        # After matching, any detection left in detections_2_remaining is new
        new = detections_2_remaining

        # You can also format the result as needed
        differences = {
            'stayed': stayed,
            'removed': removed,
            'new': new,
        }

        # print(f'Compared runs: {differences}')
        self.db.add_compared_run(field_1, run_id_1, run_id_2)
        comparison_id = self.db.get_comparison_run(run_id_1, run_id_2)

        for diff_type, diff_list in differences.items():
            for diff_pair in diff_list:
                if len(diff_pair) != 3:
                    continue
                x, y, _ = diff_pair
                self.db.add_comparison(comparison_id[0], x, y, diff_type)

        return comparison_id