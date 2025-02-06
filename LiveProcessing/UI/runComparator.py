from math import sqrt

from Database.database_handler import DatabaseHandler


class RunComparator:
    def __init__(self, db: 'DatabaseHandler'):
        self.db = db

    def is_similar(self, det1, det2, delta=1e-2):
        """
        Compare two detections. Adjust the logic below based on what attributes your
        detection objects have (e.g. x, y coordinates, type, etc.).

        For example, if your detection is a dict or object with attributes `x` and `y`:
        """
        # Example: compare positions (and maybe a type field)
        x1, y1, class1 = det1
        x2, y2, class2 = det2

        dx = x1 - x2
        dy = y1 - y2
        distance = sqrt(dx * dx + dy * dy)
        same_type = class1 == class2
        return distance <= delta and same_type

    def compare_runs(self, run_id_1, run_id_2, delta=1e-2):
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

        # For every detection in the first run, try to find a match in the second run.
        for det1 in detections_1:
            match_found = False
            for det2 in detections_2_remaining:
                if self.is_similar(det1, det2, delta):
                    stayed.append((det1, det2))
                    # Remove the matched detection so it isn’t matched twice
                    detections_2_remaining.remove(det2)
                    match_found = True
                    break  # Assuming one-to-one matching is sufficient
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

        print(f'Compared runs: {differences}')
        self.db.add_compared_run(field_1, run_id_1, run_id_2)
        comparison_id = self.db.get_comparison_run(run_id_1, run_id_2)

        for diff_type, diff_list in differences.items():
            for diff_pair in diff_list:
                x, y, _ = diff_pair[0]
                self.db.add_comparison(comparison_id[0], x, y, diff_type)

        return comparison_id