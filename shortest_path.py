"""CSC111 Project 2: Shortest Path & Vulnerability Analysis
Computes shortest paths and calculates network impact scores by simulating stop removals.
Copyright (c) 2026 Shreyas Shastry, Anson Li, Matthew He, Alan Wen Zhuo Xue
"""
import networkx as nx
import os
from typing import Dict, List, Tuple, Any
import json
from heapq import *


def dijkstra_all_nodes(graph: list, distances: list, source: Any) -> None:
    """
    Implementation of Dijkstra's algorithm for networkx DiGraphs (directed graphs)
    Returns distance to each node from source

    Preconditions:
        - len(graph) > 0
    """
    distances[source][source] = 0
    pq = []
    heappush(pq, (0, source))

    # keep going until no shorter paths to any node can be found
    while len(pq) > 0:
        stated_cost, vertex = heappop(pq)
        if distances[source][vertex] < stated_cost:
            # vertex has already been visited
            continue

        # don't make the cache extremely large
        distances[source][vertex] = round(distances[source][vertex], 3)
        for edge in graph[vertex]:
            # edges have format (v, weight)
            n, cost = edge
            new_dist = distances[source][vertex] + cost
            if distances[source][n] > new_dist:
                distances[source][n] = new_dist
                heappush(pq, (new_dist, n))


def a_star(graph: list, source: int, dest: int, heuristic: list, removed: int = None) -> Tuple[float, list[Any]]:
    """
    Implementation of A* algorithm for networkx DiGraphs (directed graphs)
    Returns distance and path

    Preconditions:
        - len(graph) > 0
    """
    if source == removed or dest == removed:
        raise ValueError

    # initialize to max values
    curr_shortest = [1e9 for _ in range(len(graph))]
    # keep track of paths
    prev = [None for _ in range(len(graph))]

    curr_shortest[source] = 0
    pq = []
    heappush(pq, (heuristic[source][dest], 0, source))

    while len(pq) > 0:
        _, stated_cost, vertex = heappop(pq)
        if vertex == dest:
            # done!
            break
        if curr_shortest[vertex] < stated_cost:
            # vertex has already been visited
            continue
        for edge in graph[vertex]:
            # edges have format (v, weight)
            n, cost = edge
            if n == removed:
                continue
            if curr_shortest[n] > curr_shortest[vertex] + cost:
                curr_shortest[n] = curr_shortest[vertex] + cost
                heappush(pq, (curr_shortest[n] + heuristic[n][dest], curr_shortest[n], n))
                prev[n] = vertex

    if curr_shortest[dest] == 1e9:
        # no path
        raise ValueError

    path = [dest]
    curr = dest
    while prev[curr]:
        curr = prev[curr]
        path.append(curr)

    path.reverse()

    return curr_shortest[dest], path


def all_paths_shortest_paths(graph: list) -> list[list[float]]:
    """
    This function performs the necessary calculations to compute the shortest paths between every node to every
    other node. It stores all the stops in a 2D grid like list and output given by lst[row][column] is the travel time
    between those stops.

    Preconditions:
        - len(graph) > 0
        - All edges have a valid weight greater than 0
    """
    print("Finding shortest path between all pairs of nodes. This will take roughly:")
    print(int(0.006 * len(graph)), " seconds")
    dist = [[1e9 for _ in range(len(graph))] for _ in range(len(graph))]
    done = 0
    for v in range(len(graph)):
        done += 1
        if done % 100 == 0:
            print(f"Processing vertex {done}/{9394}...")
        dijkstra_all_nodes(graph, dist, v)

    return dist


def handle_precomputed_apsp(apsp: list = None) -> Any | None:
    """
    Loads APSP save if exists, or writes APSP to save
    """
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, 'data')
    if not apsp:
        if os.path.exists(os.path.join(data_dir, 'precomputed_apsp.json')):
            with open(os.path.join(data_dir, 'precomputed_apsp.json'), "r") as f:
                all_shortest_paths = json.load(f)
                return all_shortest_paths
        return None

    with open(os.path.join(data_dir, 'precomputed_apsp.json'), "w") as f:
        json.dump(apsp, f)
        return None


def compute_impact_scores(graph: nx.DiGraph, sample_pairs: List[Tuple[str, str]]) -> Dict[str, float]:
    """
    Computes an impact score for every node in the network by simulating its removal.

    This function utilizes Dijkstra's Algorithm to find baseline commute times for a sample
    of Origin-Destination pairs. It then iteratively disables each stop in the network, identifies
    the affected commuters, and recalculates their new shortest path to determine the
    average delay caused by that specific failure.

    Preconditions:
        - len(sample_pairs) > 0
        - len(graph.nodes) > 0
        - all(u in graph.nodes and v in graph.nodes for u, v in sample_pairs)
    """

    nodes = list(graph.nodes())
    num_stops = len(nodes)
    node_mapping = {nodes[i]: i for i in range(num_stops)}
    # Establish all the keys for stops to be defined in the dict to avoid key errors
    impact_scores = {stop: 0.0 for stop in nodes}
    edge_graph = []
    for v in nodes:
        edges = graph.edges(v, data="weight")
        edge_graph.append([(node_mapping[e[1]], e[2]) for e in edges])

    print("Calculating baseline routes for our sample pairs...")
    # load or compute APSP for heuristic
    all_shortest_paths = handle_precomputed_apsp()
    if not all_shortest_paths:
        all_shortest_paths = all_paths_shortest_paths(edge_graph)
        handle_precomputed_apsp(all_shortest_paths)

    # list of trips with (origin, destination, original travel time) disrupted by each stop
    affected_trips = {i: [] for i in range(num_stops)}
    # find the shortest path from each origin to destination without disruptions
    for origin, dest in sample_pairs:
        origin = node_mapping[origin]
        dest = node_mapping[dest]
        try:
            length, path = a_star(edge_graph, origin, dest, all_shortest_paths)
            for stop in path:
                # add trip to affected trips list for each stop in path
                affected_trips[stop].append((origin, dest, length))
        except ValueError:
            continue

    print("Simulating detours and calculating travel delays...")

    # keep track of trips that still work (albeit delayed) and trips that are severed
    works = 0
    severed = 0
    for i, stop_to_remove in enumerate(nodes):
        removed = node_mapping[stop_to_remove]
        # Print an update every 5% of stops as a status check
        if (i + 1) % (num_stops // 20) == 0 or i + 1 == num_stops:
            print(f"Processing stop {i + 1}/{num_stops}...")
            print("Works: ", works)
            print("Severed: ", severed)

        total_delay = 0.0

        # Calculate the detours using our custom-made A-star Algorithm
        for origin, dest, orig_length in affected_trips[removed]:
            try:
                new_length, _ = a_star(edge_graph, origin, dest, all_shortest_paths, removed)
                total_delay += (new_length - orig_length)
                works += 1
            except ValueError:
                # Add a heavy time penalty if the route is completely severed
                total_delay += 120.0
                severed += 1

        # Average the delay across all sample pairs to compute the impact score for the station
        impact_scores[stop_to_remove] = total_delay / len(sample_pairs)

    return impact_scores


if __name__ == '__main__':
    import doctest

    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['networkx', 'os', 'typing', 'json', 'heapq'],
        'allowed-io': ['all_paths_shortest_paths', 'compute_impact_scores'],
        'max-line-length': 120,
        'disable': ['E1136', 'E9989', 'W0401', 'R1714', 'R0914', 'E9988', 'C0411']
    })
