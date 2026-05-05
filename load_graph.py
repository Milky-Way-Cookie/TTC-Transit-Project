"""CSC111 Project 2: Graph Loader
This function helps with loading the transit graph and precomputed impact scores for the main file
Copyright (c) 2026 Shreyas Shastry, Anson Li, Matthew He, Alan Wen Zhuo Xue
"""

import os
import json
import random
import networkx as nx
from shortest_path import compute_impact_scores
from graph_builder import TransitGraph


def load_graph(data_dir: str) -> TransitGraph:
    """
    Initializes the TransitGraph and loads the stops and stop_times data.

    Preconditions:
        - data_dir != ''
        - os.path.exists(os.path.join(data_dir, 'stops.txt'))
        - os.path.exists(os.path.join(data_dir, 'stop_times.txt'))
    """
    transit_graph = TransitGraph()
    transit_graph.load_stops(os.path.join(data_dir, 'stops.txt'))
    transit_graph.load_stop_times(os.path.join(data_dir, 'stop_times.txt'))
    print(f"Graph loaded: {len(transit_graph.graph.nodes())} stops, {len(transit_graph.graph.edges())} edges.")
    return transit_graph


def load_impact_scores(transit_graph: TransitGraph, data_dir: str) -> dict[str, float]:
    """
    Loads precomputed impact scores from a JSON file, or computes them if the file does not exist.

    Preconditions:
        - data_dir != ''
        - len(transit_graph.graph.nodes()) > 0
    """
    output_file = os.path.join(data_dir, 'precomputed_impact_scores.json')

    if os.path.exists(output_file):
        print(f"Loading precomputed impact scores from {output_file}...")
        with open(output_file, 'r') as f:
            impact_scores = json.load(f)
        return impact_scores
    else:
        stops = list(transit_graph.graph.nodes())
        num_pairs = 1000
        sample_pairs = set()
        print("Finding REACHABLE origin-destination pairs. This might take a minute...")

        attempts = 0
        while len(sample_pairs) < num_pairs and attempts < 10000:
            attempts += 1
            a, b = random.sample(stops, 2)
            if nx.has_path(transit_graph.graph, a, b):
                sample_pairs.add((a, b))

        print("Computing impact scores (calculating real detours)...")
        if not sample_pairs:
            print("Error: Could not find any reachable origin-destination pairs.")
            raise ValueError
        impact_scores = compute_impact_scores(transit_graph.graph, list(sample_pairs))

        with open(output_file, 'w') as f:
            json.dump(impact_scores, f)
        print(f"Saved impact scores to {output_file}")
        return impact_scores


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': ['os', 'json', 'random', 'shortest_path', 'graph_builder', 'networkx'],
        'allowed-io': ['load_graph', 'load_impact_scores'],
        'max-line-length': 120
    })
