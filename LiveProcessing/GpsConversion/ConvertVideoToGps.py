from pyproj import Geod

class GPSMapper:
    def __init__(self, start_gps, end_gps, frame_width, frame_height):
        """
        Initialize the GPSMapper class with necessary parameters.

        Args:
        - start_gps (tuple): (latitude, longitude) of the starting point.
        - end_gps (tuple): (latitude, longitude) of the ending point.
        - frame_width (int): Width of the video frame.
        - frame_height (int): Height of the video frame.
        """
        self.start_gps = start_gps
        self.end_gps = end_gps
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.geod = Geod(ellps="WGS84")  # WGS84 ellipsoid (default)

        # Precompute total geodesic distance and azimuths
        self.azimuth, _, self.total_distance = self.geod.inv(
            start_gps[1], start_gps[0], end_gps[1], end_gps[0]
        )

    def normalize_coords(self, centers):
        """
        Normalize video frame coordinates to the range [0, 1].

        Args:
        - centers (list of tuples): List of (x, y) video frame coordinates.

        Returns:
        - list of tuples: Normalized coordinates [(nx, ny), ...].
        """
        return [(x / self.frame_width, y / self.frame_height) for x, y in centers]

    def map_to_gps(self, centers, classes):
        """
        Map video frame coordinates to GPS coordinates.

        Args:
        - centers (list of tuples): List of (x, y) video frame coordinates.
        - classes (list of int): List of class labels (e.g., 0 = crop, 1 = weed).

        Returns:
        - list of tuples: [(latitude, longitude, class_label), ...].
        """
        normalized_centers = self.normalize_coords(centers)
        gps_coords = []

        for (nx, ny), cls in zip(normalized_centers, classes):
            # Calculate the distance along the geodesic line
            distance = nx * self.total_distance

            # Get the GPS point at the calculated distance
            lon, lat, _ = self.geod.fwd(
                self.start_gps[1], self.start_gps[0], self.azimuth, distance
            )
            gps_coords.append((lat, lon, cls))

        return gps_coords
