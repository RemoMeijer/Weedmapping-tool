from Database.database_handler import DatabaseHandler


class RunComparator:
    def __init__(self, db: 'DatabaseHandler'):
        self.db = db

    def compare_runs(self, run_id_1, run_id_2):
        detections_1 = self.db.get_detections_by_run_id(run_id_1)
        detections_2 = self.db.get_detections_by_run_id(run_id_2)

        differences = []
        print('Comparing runs...')

        return differences
