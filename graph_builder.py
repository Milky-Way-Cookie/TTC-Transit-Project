"""
CSC111 Project 2: Graph Builder
This file parses GTFS data from the TTC dataset to construct a directed graph of the Toronto transit network.
Copyright (c) 2026 Shreyas Shastry, Anson Li, Matthew He, Alan Wen Zhuo Xue
"""

from typing import Optional
import pandas as pd
import networkx as nx


class TransitGraph:
    """A directed graph representing a public transit network.

    Instance Attributes:
        - graph: A directed graph using the nx library where nodes are stops and edges represent travel time in minutes.
        - stops: A dictionary mapping stop IDs to a tuple as follows: (latitude, longitude, stop_name).

    Representation Invariants:
        - all(isinstance(stop_id, str) for stop_id in self.stops)
        - all(stop_id in self.graph.nodes for stop_id in self.stops)
        - all(self.graph[u][v]['weight'] >= 0 for u, v in self.graph.edges)
    """
    graph: nx.DiGraph
    stops: dict[str, tuple[float, float, str]]

    def __init__(self) -> None:
        """Initialize a new, empty TransitGraph."""
        self.graph = nx.DiGraph()
        self.stops = {}

    def load_stops(self, stops_file: str) -> None:
        """
        Parses the stops.txt file and populate the graph nodes and stops dictionary.

        Preconditions:
            - stops_file != ''
            - stops_file is a valid path to a CSV file with 'stop_id', 'stop_lat', 'stop_lon', 'stop_name' columns
        """
        df = pd.read_csv(
            stops_file,
            usecols=["stop_id", "stop_lat", "stop_lon", "stop_name"],
            dtype={"stop_id": str, "stop_name": str}
        )
        # convert to numpy to make it faster
        cols = df.columns.tolist()
        lat = cols.index("stop_lat")
        lon = cols.index("stop_lon")
        name = cols.index("stop_name")
        s_id = cols.index("stop_id")

        # create vertices in graph with stop data
        df = df.values
        for i in range(len(df)):
            row = df[i]
            stop_id = row[s_id]
            self.stops[stop_id] = (row[lat], row[lon], str(row[name]))
            self.graph.add_node(stop_id, pos=(row[lon], row[lat]), name=str(row[name]))

    @staticmethod
    def _time_to_seconds(t: str) -> Optional[int]:
        """
        Converts a HH:MM:SS string into total seconds from midnight. This is used to clean up our dataset values

        >>> TransitGraph._time_to_seconds("01:30:45")
        5445
        >>> TransitGraph._time_to_seconds("25:00:00")
        90000

        Preconditions:
            - isinstance(t, str)
            - len(t.split(':')) == 3
        """
        try:
            h, m, s = map(int, t.split(":"))
            return h * 3600 + m * 60 + s
        except ValueError:
            return None

    def load_stop_times(self, stop_times_file: str) -> None:
        """
        Parses the stop_times.txt file to build directed edges between consecutive stops.

        Preconditions:
            - stop_times_file != ''
            - stop_times_file is a valid path to a CSV file
            - self.graph has been populated with nodes (load_stops has been called)
        """
        # This assumes stop_times.txt is grouped by trip_id. If your computer cannot do 1000000 line chunks
        # You may decrease the chunk number to like 4 000 if needed
        chunk_size = 1000000
        prev_rows = {}
        chunk_count = 0

        # We did this in chunks since the file is extremely large
        for chunk in pd.read_csv(
                stop_times_file,
                usecols=["trip_id", "stop_id", "arrival_time", "stop_sequence"],
                dtype={"trip_id": str, "stop_id": str, "arrival_time": str, "stop_sequence": int},
                chunksize=chunk_size
        ):
            chunk_count += 1
            if chunk_count % 1 == 0:
                print(f"Processing chunk {chunk_count}...")

            # We sort the chunks just in case the file is not fully sorted
            # This also "cleans" the data in case there is any missing data that is corrupt and excludes the bad data
            # and assigns chunk to only include the good data that can be read
            chunk = chunk.sort_values(["trip_id", "stop_sequence"])
            chunk["time_sec"] = chunk["arrival_time"].apply(self._time_to_seconds)
            chunk = chunk[chunk["time_sec"].notna()]
            cols = chunk.columns.tolist()
            t_col = cols.index("time_sec")
            trip_col = cols.index("trip_id")
            s_col = cols.index("stop_id")

            # convert to numpy to make it faster
            chunk = chunk.values

            for i in range(len(chunk)):
                time_sec = chunk[i, t_col]
                trip_id = chunk[i, trip_col]
                stop_id = chunk[i, s_col]

                if trip_id in prev_rows:
                    prev_stop, prev_time = prev_rows[trip_id]

                    # Assigns the travel time to the edge by taking the difference in travel time in minutes
                    travel_time = (time_sec - prev_time) / 60

                    # Verifies that the travel time is not 0 (cannot be negative time or teleport instantly)
                    # Then add the edge data
                    if travel_time > 0:
                        edge_data = self.graph.get_edge_data(prev_stop, stop_id)
                        if not edge_data or travel_time < edge_data["weight"]:
                            self.graph.add_edge(prev_stop, stop_id, weight=travel_time)

                prev_rows[trip_id] = (stop_id, time_sec)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['pandas', 'networkx', 'typing'],
        'allowed-io': ['TransitGraph.load_stop_times'],
        'max-line-length': 120,
        'disable': ['E1136', 'W0622', 'E9994', 'R0914'],
        'max-nested-blocks': 7
    })