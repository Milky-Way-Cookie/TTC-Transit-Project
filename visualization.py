"""CSC111 Project 2: Visualization
Generates interactive MapLibre visualizations using Plotly for the TTC network you can view the graph with
this function.
Copyright (c) 2026 Shreyas Shastry, Anson Li, Matthew He, Alan Wen Zhuo Xue
"""

from typing import Dict, List, Tuple
import networkx as nx
import plotly.graph_objects as go


def create_transit_map(graph: nx.DiGraph, impact_scores: Dict[str, float], stops: Dict[str, Tuple[float, float, str]]) -> go.Figure:
    """
    Takes the impact score file you generate with the algorithm and constructs a map of
    the city of Toronto using the data provided, stations increase in size based on their impact
    score and a colourmap is provided to differentiate the scores.

    Preconditions:
        - all(stop_id in impact_scores for stop_id in stops)
        - all(node in stops for node in graph.nodes)
    """
    fig = go.Figure()

    # Stores the coordinates of the midpoints and edges
    edge_lats, edge_lons = [], []
    mid_lats, mid_lons, mid_texts = [], [], []

    # Loops through the graphs edges to obtain edge info for visualization
    for start, end, info in graph.edges(data=True):
        start_lat, start_lon, start_name = stops[start]
        end_lat, end_lon, end_name = stops[end]

        travel_dur = info.get('weight', 0)
        hover_tag = start_name + "->" + end_name + "<br>Travel Duration: " + str(round(travel_dur, 2)) + " mins"

        # Creates the list that will be used to connect each station with lines
        edge_lats.append(start_lat)
        edge_lats.append(end_lat)
        edge_lats.append(None)
        edge_lons.append(start_lon)
        edge_lons.append(end_lon)
        edge_lons.append(None)

        # Source: We were unable to find a plotly feature to display hover info for edges nicely without
        # having display conflicts between edges and vertices
        # Gemini suggested the idea of using midpoints of edges to display hover data by using invisible vertices
        # Implementation and code calculations for midpoints were written by us
        mid_lats.append((start_lat + end_lat) / 2)
        mid_lons.append((start_lon + end_lon) / 2)
        mid_texts.append(hover_tag)

    # Drops invisible dots precisely in the middle of the lines for hovering
    # Source: Gemini for lines 58-59 to find correct parameters to use to specify dot shapes and find
    # Specific parameters and rgba values to properly display edge hover text
    fig.add_trace(go.Scattermap(
        lat=mid_lats,
        lon=mid_lons,
        mode='markers',
        marker=dict(size=6, color='rgba(0,0,0,0)'),
        text=mid_texts,
        hoverinfo='text',
        showlegend=False
    ))

    # Draw the cyan lines edges connecting each station to its neighbours
    # Source: Gemini for lines 72-73 we had trouble finding the corresponding mode for edges as
    # most of the visualizations have the same "fig.add_trace" format with minor parameter changes
    # so we used it to quickly find the proper way to display an edge and choose a nice colour for the map
    fig.add_trace(go.Scattermap(
        lat=edge_lats,
        lon=edge_lons,
        mode='lines',
        line=dict(width=2, color='cyan'),
        hoverinfo='none',
        showlegend=False
    ))

    # Iterates through the stops paramater and collects latitude, longitude, and name and then
    # calculates the size and color based on impact score, and also adding text for hover info
    lats, lons, texts, sizes, colors = [], [], [], [], []
    for stop_id, (lat, lon, name) in stops.items():
        lats.append(lat)
        lons.append(lon)

        impact = impact_scores.get(stop_id, 0)
        texts.append(f"<b>{name}</b><br>ID: {stop_id}<br>Impact: {impact:.2f} mins")

        calculated_size = 5 + (impact * 25)
        sizes.append(min(25.0, calculated_size))
        colors.append(impact)

    # Source: Gemini for lines 101-109, the legend for the colours of the vertices was initially too large
    # to fit and was covering a button that can enable/disable parts of the graph. We used it to address
    # how we can fix that issue, which gave us the parameters len and y which we tweaked ourselves to fit the legend
    fig.add_trace(go.Scattermap(
        lat=lats,
        lon=lons,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            colorscale='Inferno',
            showscale=True,
            colorbar=dict(
                title="Impact (mins)",
                len=0.95,  # Shrinks the bar to 95% of the screen height
                y=0.5  # Shifts it down away from the top-right toolbar
            ),
            opacity=0.7
        ),
        text=texts,
        hoverinfo='text'
    ))

    fig.update_layout(
        map=dict(
            style="open-street-map",
            center=dict(lat=43.7, lon=-79.4),
            zoom=11.5
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        title="Toronto Transit Network"
    )

    return fig


def show_shortest_path(graph: nx.DiGraph, orig_path: List[str], new_path: List[str],
                       stops: Dict[str, Tuple[float, float, str]], disabled_stop: str) -> go.Figure:
    """
    Visualization for the Djikstra's algorithm option for showing the detour for the
    interactive map comparing the path for when a stop is disabled and what
    the shortest detour looks like.

    Preconditions:
        - len(orig_path) >= 2
        - len(new_path) >= 2
        - disabled_stop in orig_path
        - all(stop in stops for stop in orig_path)
        - all(stop in stops for stop in new_path)
    """
    fig = go.Figure()

    # Adds all stops into 2 lists based on latitude and longitude
    lats, lons = [], []
    for _, (lat, lon, _) in stops.items():
        lats.append(lat)
        lons.append(lon)

    # Adds all the stops has gray vertices
    fig.add_trace(go.Scattermap(
        lat=lats,
        lon=lons,
        mode='markers',
        marker=dict(size=4, color='lightgray'),
        hoverinfo='none',
        showlegend=False
    ))

    # Does the same thing as before but just for the stops in the original path
    orig_lats, orig_lons, orig_texts = [], [], []
    for stop in orig_path:
        lat, lon, name = stops[stop]
        orig_lats.append(lat)
        orig_lons.append(lon)
        orig_texts.append("<b>" + str(name) + "</b><br>ID: " + str(stop))

    # Source: Gemini for line 173-175, originally we wrote marker and lines seperately, but it suggested an
    # optimization to combine them as 1 since they are connected to each other so we decided to go with that
    fig.add_trace(go.Scattermap(
        lat=orig_lats,
        lon=orig_lons,
        mode='markers+lines',
        marker=dict(size=20, color='blue'),
        line=dict(width=12, color='blue'),
        text=orig_texts,
        hoverinfo='text',
        name='Original Route'
    ))

    # Similar to the earlier method of adding invisible dots for hover text
    orig_mid_lats, orig_mid_lons, orig_mid_texts = [], [], []
    for i in range(len(orig_path) - 1):
        start, end = orig_path[i], orig_path[i + 1]
        start_lat, start_lon, start_name = stops[start]
        end_lat, end_lon, end_name = stops[end]

        # Grabs the weight using the weight key returns the weight if it exists otherwise assign it as 0
        edge_data = graph.get_edge_data(start, end)
        travel_dur = edge_data.get('weight', 0) if edge_data else 0

        # Source: Gemini line 197 and line 239 we wanted the text to look nice for the user so we asked it to display
        # the text nicely in the hover display using some HTML formatting
        orig_mid_lats.append((start_lat + end_lat) / 2)
        orig_mid_lons.append((start_lon + end_lon) / 2)
        orig_mid_texts.append(
            f"<span style='color:dodgerblue'><b>Original Route</b></span><br>{start_name} -> {end_name}<br>Travel Duration: {travel_dur:.1f} mins")

    fig.add_trace(go.Scattermap(
        lat=orig_mid_lats,
        lon=orig_mid_lons,
        mode='markers',
        marker=dict(size=10, color='rgba(0,0,0,0)'),
        text=orig_mid_texts,
        hoverinfo='text', showlegend=False
    ))

    # Red Detour Path same as the blue one except the path is different
    det_lats, det_lons, det_texts = [], [], []
    for stop in new_path:
        lat, lon, name = stops[stop]
        det_lats.append(lat)
        det_lons.append(lon)
        det_texts.append("<b>" + str(name) + "</b><br>ID: " + str(stop))

    fig.add_trace(go.Scattermap(
        lat=det_lats,
        lon=det_lons,
        mode='markers+lines',
        marker=dict(size=12, color='red'),
        line=dict(width=4, color='red'),
        text=det_texts, hoverinfo='text', name='Detour Route'
    ))

    # Same invisible dot logic for hovertext as before
    det_mid_lats, det_mid_lons, det_mid_texts = [], [], []
    for i in range(len(new_path) - 1):
        start, end = new_path[i], new_path[i + 1]
        start_lat, start_lon, start_name = stops[start]
        end_lat, end_lon, end_name = stops[end]

        # Grabs the weight using the weight key returns the weight if it exists otherwise assign it as 0
        edge_data = graph.get_edge_data(start, end)
        travel_dur = edge_data.get('weight', 0) if edge_data else 0

        det_mid_lats.append((start_lat + end_lat) / 2)
        det_mid_lons.append((start_lon + end_lon) / 2)
        det_mid_texts.append(
            f"<span style='color:red'><b>Detour Route</b></span><br>{start_name} -> {end_name}<br>Travel Duration: {travel_dur:.1f} mins")

    fig.add_trace(go.Scattermap(
        lat=det_mid_lats,
        lon=det_mid_lons,
        mode='markers',
        marker=dict(size=10, color='rgba(0,0,0,0)'),
        text=det_mid_texts,
        hoverinfo='text',
        showlegend=False
    ))

    # Start, End, and Disabled Stop Markers to clearly highlight them on the map
    start_stop, end_stop = orig_path[0], orig_path[-1]
    start_lat, start_lon, start_name = stops[start_stop]
    end_lat, end_lon, end_name = stops[end_stop]
    dis_lat, dis_lon, dis_name = stops[disabled_stop]

    # Highlight the starting station in green
    fig.add_trace(go.Scattermap(
        lat=[start_lat],
        lon=[start_lon],
        mode='markers',
        marker=dict(size=20, color='green'),
        text=["<b>START: " + str(start_name) + "</b><br>ID: " + str(start_stop)],
        hoverinfo='text',
        name='Start Location'
    ))

    # Highlight the destination station in yellow
    fig.add_trace(go.Scattermap(
        lat=[end_lat],
        lon=[end_lon],
        mode='markers',
        marker=dict(size=20, color='yellow'),
        text=["<b>END: " + str(end_name) + "</b><br>ID: " + str(end_stop)],
        hoverinfo='text',
        name='End Location'
    ))

    # Highlight the disabled stop in black
    fig.add_trace(go.Scattermap(
        lat=[dis_lat],
        lon=[dis_lon],
        mode='markers',
        marker=dict(size=20, color='black'),
        text=["<b>DISABLED STOP: " + str(dis_name) + "</b><br>ID: " + str(disabled_stop)],
        hoverinfo='text',
        name='Disabled Stop'
    ))

    fig.update_layout(
        map=dict(
            style="open-street-map",
            center=dict(lat=43.7, lon=-79.4),
            zoom=11.5
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        title="Toronto Transit Network"
    )

    return fig


if __name__ == '__main__':
    import doctest

    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': ['networkx', 'plotly.graph_objects', 'typing'],
        'allowed-io': [],
        'max-line-length': 180,
        'disable': ['E1136', 'R0914', 'R1735', 'C0411']
    })
