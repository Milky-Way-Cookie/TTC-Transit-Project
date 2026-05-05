# CSC111-Project-2

# Modelling and Analyzing the Toronto Urban Public Transit Network

**Team Members:** Shreyas Shastry, Anson Li, Matthew He, Alan Wen Zhuo Xue

## Project Overview
This project models the Toronto Transit Commission (TTC) network as a weighted directed graph to identify the system's most critical stations. By computationally simulating disruptions (by disabling one stop at a time) and recalculating shortest paths using our custom implemented Dijkstra's algorithm, we assign an "impact score" to each stop. The results are visualized geographically using Plotly MapLibre to highlight the most essential transit hubs with the feature to view all stations and their scores as a whole or to simulate our algorithm in action when 1 stop is broken.

## Prerequisites and Installation
Your machine must have **Python 3.13.5** installed. 

1. Clone or extract this project directory to your local machine.
2. Install the required external libraries by running:
   ```bash
   pip install -r requirements.txt
