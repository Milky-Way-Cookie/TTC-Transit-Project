"""CSC111 Project 2: Main Runner
This file runs all of our files for this project into a centralized program.
It is responsible for handling user input, map generation, and detours demonstration
Copyright (c) 2026 Shreyas Shastry, Anson Li, Matthew He, Alan Wen Zhuo Xue
"""

import os
import random
import networkx as nx
from load_graph import load_graph, load_impact_scores
from visualization import create_transit_map, show_shortest_path


def main() -> None:
    """ Executes the TTC Disruption Simulator.

        This function is how you should fun our program. It loads the data from our dataset
        initializes the transit graph, computes the network vulnerability impact scores,
        and launches an interactive terminal oriented interface for you to explore the data
        and simulate custom detours to see the Dijkstra algorithm in action.

        Preconditions:
        - The required GTFS files ('stops.txt' and 'stop_times.txt') are downloaded and exist in the data folder.
    """

    print("Loading TTC transit data...")
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, 'data')
    if not os.path.isdir(data_dir):
        print(
            "Error: 'data/' folder not found. Please ensure you have extracted " +
            "the GTFS zip file into a folder named 'data/'.")
        return

    # Loads the graphs and impact scores needed to run main
    transit_graph = load_graph(data_dir)
    impact_scores = load_impact_scores(transit_graph, data_dir)

    print("\n==================================")
    print("  TTC PATH FINDING ALGORITHM RUNNER 2026")
    print("==================================")

    # While loop logic for testing our code features
    while True:
        print("\nMain Menu:")
        print("1. View the Network Impact Score Map")
        print("2. Simulate a Custom Route Detour")
        print("3. Auto-fetch a Valid Stop IDs for Dijkstra Demonstration (Get IDs for option 2)")
        print("4. Quit")
        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            print("Generating visualization in the browser please wait a bit...")
            # Creates the transit map with all stations and their impact scores and then redirects to browser
            fig = create_transit_map(transit_graph.graph, impact_scores, transit_graph.stops)
            fig.show()

        elif choice == '2':
            # Choose valid stop IDS to demonstrate alternate path finding, strips all accidental whitespace
            print("\n--- Custom Detour Demonstration ---")
            orig = input("Enter Origin Stop ID: ").strip()
            dest = input("Enter Destination Stop ID: ").strip()
            disable = input("Enter Stop ID to disable: ").strip()

            # Prevents user from inputting any IDs that do not make sense, either outside dataset or
            # The start or end stop is inputted as disabled
            if orig not in transit_graph.stops or dest not in transit_graph.stops or disable not in transit_graph.stops:
                print("Error: One or more Stop IDs do not exist in the dataset.")
                continue
            if disable == orig or disable == dest:
                print("Error: Cannot calculate a detour if the Origin or Destination itself is disabled.")
                continue

            try:
                # Check if a baseline path exists, you may switch between our Dijkstra algorithm and the
                # nx.shortest_path built-in library function to compare if you wish, but both will be the same output
                orig_path = nx.shortest_path(transit_graph.graph, orig, dest, weight="weight")
                orig_time = nx.shortest_path_length(transit_graph.graph, orig, dest, weight="weight")
            except (nx.NetworkXNoPath, nx.NodeNotFound):  # If for some reason there is no path, raise an error
                print("\nError: No path exists between those stops in the normal network.")
                continue
            # If disabled stop isn't in the shortest path, then no detour is needed
            if disable not in orig_path:
                print(f"\nStop {disable} is not on the shortest route between {orig} and {dest}.")
                print("No detour required.")
                continue

            # Creates a subgraph with the disabled stop removed and calculates an alternate detour to destination
            active_nodes = set(transit_graph.graph.nodes())
            active_nodes.remove(disable)
            temp_graph = transit_graph.graph.subgraph(active_nodes)

            try:
                # Try to calculate the alternate detour path once again, you may switch between our custom algorithm
                # or use the built-in algorithm for pathfindingif you wish
                new_path = nx.shortest_path(temp_graph, orig, dest, weight="weight")
                new_time = nx.shortest_path_length(temp_graph, orig, dest, weight="weight")

                print("\nDetour Calculation Successful")
                print(f"Original Travel Time: {orig_time:.1f} mins")
                print(f"New Travel Time: {new_time:.1f} mins (+{new_time - orig_time:.1f} mins)")
                print("Launching Detour Map...")

                path_fig = show_shortest_path(transit_graph.graph, orig_path, new_path, transit_graph.stops, disable)
                path_fig.show()

            except (nx.NetworkXNoPath, nx.NodeNotFound):
                print("\nDisabling that stop completely severed the route. No alternative path available.")

        # This feature is to help the TA find a valid list of IDs to test our algorithm for Dijkstra
        # We use the built-in algorithms for Dijkstras algorithm for this so you can verify that
        # The example given by the built-in algorithm works with our custom algorithm
        elif choice == '3':
            print("\nSearching for a valid detour scenario...")
            nodes_list = list(transit_graph.graph.nodes())
            found_test = False

            # Randomly chooses 2 random stops in the TTC dataset until we find a valid combination
            for _ in range(10000):
                orig, dest = random.sample(nodes_list, 2)
                try:
                    orig_path = nx.shortest_path(transit_graph.graph, orig, dest, weight="weight")
                    orig_time = nx.shortest_path_length(transit_graph.graph, orig, dest, weight="weight")

                    # If no errors occur and the path is at least 6 stops apart (for the result to be clear),
                    # set the broken stop to be in the
                    # middle of the route for a valid broken stop in the original path
                    if len(orig_path) > 6:
                        broken_stop = orig_path[len(orig_path) // 2]

                        # Makes a subgraph of the original graph with the chosen stop disabled
                        active_nodes = set(transit_graph.graph.nodes())
                        active_nodes.remove(broken_stop)
                        temp_g = transit_graph.graph.subgraph(active_nodes)

                        new_time = nx.dijkstra_path_length(temp_g, orig, dest, weight="weight")
                        delay = new_time - orig_time

                        if 3.0 < delay < 30.0:
                            print("\n--- Detour Scenario Found ---")
                            print(f"Origin ID: {orig}")
                            print(f"Destination ID: {dest}")
                            print(f"Stop to Disable: {broken_stop}")
                            print(f"Estimated Delay: +{delay:.1f} mins")
                            found_test = True
                            break
                # If an error occurs for some reason just continue
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

            # This should never happen but if it does just try again it should work 99% of the time
            if not found_test:
                print("Could not locate a suitable scenario within iteration limit. Please try again.")

        elif choice == '4':
            print("Exiting Simulator.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
