# simulation.py

import osmnx as ox
import networkx as nx
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from typing import List, Dict, Any

from main_agent import MainAgent
from delivery_agent import DeliveryAgent
from package import Package

MAP_QUERY = 'Cau Giay District, Hanoi, Vietnam' 

def update_visualization(graph: nx.Graph, supervisor: MainAgent, ax: plt.Axes) -> list:
    # (This is a presentation/view function)
    artists = [] 
    available_agents_coords = [(graph.nodes[a.location]['x'], graph.nodes[a.location]['y']) for a in supervisor.agents if a.status == 'available']
    busy_agents_coords = [(graph.nodes[a.location]['x'], graph.nodes[a.location]['y']) for a in supervisor.agents if a.status == 'busy']
    charging_agents_coords = [(graph.nodes[a.location]['x'], graph.nodes[a.location]['y']) for a in supervisor.agents if a.status == 'returning_to_charge']
    
    if available_agents_coords:
        artists.append(ax.scatter(*zip(*available_agents_coords), c='blue', s=50, label='Available Agents', zorder=5))
    if busy_agents_coords:
        artists.append(ax.scatter(*zip(*busy_agents_coords), c='orange', s=50, label='Busy Agents', zorder=5))
    if charging_agents_coords:
        artists.append(ax.scatter(*zip(*charging_agents_coords), c='grey', s=50, label='Returning to Charge', zorder=5))

    for agent in supervisor.agents:
        if agent.path: 
            route_nodes = [agent.location] + agent.path 
            route_coords = [(graph.nodes[node]['x'], graph.nodes[node]['y']) for node in route_nodes]
            path_color = 'orange'
            if agent.status == 'returning_to_charge':
                path_color = 'grey'
            line = ax.plot(*zip(*route_coords), color=path_color, linewidth=2, zorder=4)
            artists.extend(line) 
    
    active_dropoffs = []
    for a in supervisor.agents:
        if a.status == 'busy':
            active_dropoffs.extend(a.dropoff_order) 
        elif a.status == 'available' and len(a.packages_on_board) > 0:
            active_dropoffs.extend([pkg.dropoff_location for pkg in a.packages_on_board])
    active_dropoffs = list(set(active_dropoffs))

    if active_dropoffs:
        dropoff_coords = [(graph.nodes[node]['x'], graph.nodes[node]['y']) for node in active_dropoffs]
        artists.append(ax.scatter(*zip(*dropoff_coords), c='red', s=100, label='Dropoff', zorder=6, marker='X'))
        
    return artists

def run_simulation():
    
    print(f"Loading map from OpenStreetMap ({MAP_QUERY})...")
    graph_directional = ox.graph_from_place(MAP_QUERY, network_type='drive')
    print("Converting map to undirected (ignoring one-way streets)...")
    graph = graph_directional.to_undirected() 
    graph = nx.convert_node_labels_to_integers(graph)
    nodes = list(graph.nodes)
    print(f"Map has {len(graph.nodes)} nodes")

    NUM_AGENTS = 3   
    NUM_PACKAGES = 20
    MIN_WORKING_BUFFER_PERCENT = 0.3

    supervisor = MainAgent(graph) 
    supervisor.create_agents(NUM_AGENTS, MIN_WORKING_BUFFER_PERCENT)
    
    all_tasks = []
    print(f"\nCreating {NUM_PACKAGES} packages...")
    for i in range(NUM_PACKAGES):
        while True:
            dropoff = random.choice(nodes)
            if (dropoff != supervisor.location and 
                nx.has_path(graph, supervisor.location, dropoff)):
                break
        package = Package(package_id=i + 1, dropoff_location=dropoff, pickup_location=supervisor.location)
        all_tasks.append(package)

    supervisor.add_tasks(all_tasks)
    
    plt.ion() 
    fig, ax = plt.subplots(figsize=(12, 12))
    
    print("Drawing map...")
    ox.plot_graph(
        graph, ax=ax, show=False, close=False, 
        bgcolor='#FFFFFF', node_color='grey', node_size=1, edge_linewidth=0.3, edge_color='#BBBBBB'
    )
    
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.85, box.height])

    depot_node = supervisor.location
    ax.scatter(
        graph.nodes[depot_node]['x'], graph.nodes[depot_node]['y'], 
        c='green', s=200, label='Main Agent (Depot)', zorder=6, marker='*'
    )
    print("Drawing map completed.")
    
    dynamic_artists = [] 
    time_step = 0

    # main loop
    while any(p.status != 'delivered' and p.status != 'cancelled' for p in all_tasks):
        print(f"\n--- Time Step: {time_step} ---")

        # Print a summary of all agent states at the start of the time step
        for a in supervisor.agents:
            if a.status == 'busy': 
                next_stop = f"Node {a.dropoff_order[0]}" if a.dropoff_order else "Depot"
                print(f"  > Agent {a.id} [BUSY]: Moving to {next_stop} ({len(a.packages_on_board)} packages left). (Battery: {a.current_battery:.1f})")
            elif a.status == 'returning_to_charge':
                print(f"  > Agent {a.id} [RETURNING]: Returning to depot. (Battery: {a.current_battery:.1f})")
            elif a.status == 'available' and a.location == supervisor.location:
                if len(a.packages_on_board) > 0:
                     print(f"  > Agent {a.id} [COLLECTING]: At depot, holding {len(a.packages_on_board)} packages. (Battery: {a.current_battery:.1f})")
                else:
                     print(f"  > Agent {a.id} [IDLE]: At depot, waiting for tasks. (Battery: {a.current_battery:.1f})")
            elif a.status == 'available' and a.location != supervisor.location:
                 print(f"  > Agent {a.id} [WAITING]: Standing by at {a.location}. (Battery: {a.current_battery:.1f})")

        for artist in dynamic_artists:
            artist.remove()
        
        ###--- [TRIGGER FOR: Interaction Protocols] ---###
        # This line triggers the MainAgent to start the Contract Net Protocol (Bidding) if tasks are available.
        supervisor.check_and_assign_tasks()
        ###--- [END TRIGGER] ---###

        ###--- [TRIGGER FOR: Dynamic Adaptation] ---###
        # This loop is the "heartbeat" that triggers agent autonomy.
        # Each call to agent.update() allows the agent to adapt its behavior based on its internal state and environment.
        for agent in supervisor.agents:
            agent.update(
                supervisor.location, 
                MIN_WORKING_BUFFER_PERCENT, 
                supervisor.pending_tasks
            )
        ###--- [END TRIGGER] ---###
            
        dynamic_artists = update_visualization(graph, supervisor, ax)
        
        completed_count = len([p for p in all_tasks if p.status == 'delivered'])
        ax.set_title(
            f"Time: {time_step} | {completed_count}/{NUM_PACKAGES} packages delivered"
        )
        
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles)) 
        
        ax.legend(
            by_label.values(), 
            by_label.keys(), 
            loc='upper left',           
            bbox_to_anchor=(1.0, 1.0),
            frameon=True,
            facecolor='white',
            framealpha=1.0
        )

        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(0.1) 
        
        time_step += 1

    print(f"\nSimulation Completed")
    print(f"Delivered all packages in {time_step} time steps.")
    plt.ioff() 
    ax.set_title(f"Delivery completed after {time_step} time steps")
    fig.canvas.draw()
    plt.show() 

if __name__ == "__main__":
    run_simulation()