# delivery_agent.py

import random
import networkx as nx
from package import Package

class DeliveryAgent:

    def __init__(self, agent_id: int, graph: nx.Graph, min_working_buffer_percent: float, start_node: int = None):
        self.id = agent_id
        self.graph = graph
        self.location = start_node if start_node else random.choice(list(graph.nodes))
        self.status = 'available'
        self.path = []  
        self.final_destination = None
        self.capacity = 5 
        self.packages_on_board: list[Package] = [] 
        self.dropoff_order: list[int] = [] 
        self.max_battery = 100
        self.current_battery = self.max_battery
        self.drain_per_meter = 0.005
        self.standby_drain_per_step = 0.1
        self.min_working_buffer_percent = min_working_buffer_percent
        print(f"Agent {self.id}: Created at node {self.location}.")

    ###--- [START: Dynamic Adaptation] ---###
    def update(self, depot_location, min_buffer_percent, pending_tasks_list: list[Package]):
        
        if self.status == 'busy':
            self.move() 
        
        elif self.status == 'available':
            
            # Dynamic Adaptation at Depot (Collecting Packages Logic)
            if self.location == depot_location:
                if self.current_battery < self.max_battery:
                    self.current_battery = self.max_battery 
                
                if len(self.packages_on_board) > 0:
                    if len(self.packages_on_board) >= self.capacity:
                        print(f"Agent {self.id}: Capacity is full ({self.capacity} packages). Start Delivering.")
                        self._plan_and_depart()
                    elif not pending_tasks_list:
                        print(f"Agent {self.id}: No more pending tasks in queue. Start Delivering with {len(self.packages_on_board)} packages.")
                        self._plan_and_depart()
                    else:
                        can_bid_any_more = False
                        for task in pending_tasks_list:
                            if self._is_task_feasible(task.dropoff_location, depot_location, min_buffer_percent):
                                can_bid_any_more = True
                                break 
                        if not can_bid_any_more:
                            print(f"Agent {self.id}: Battery is NOT sufficient for any remaining tasks.")
                            print(f"  > Departing early with {len(self.packages_on_board)} packages.")
                            self._plan_and_depart()
            
    ###--- [END: Dynamic Adaptation] ---###

    ###--- [START: Search/Optimization] ---###
    def _calculate_travel_distance(self, pickup: int, dropoff: int) -> float:
        try:
            path1_length = nx.shortest_path_length(
                self.graph, source=self.location, target=pickup, weight='length'
            )
            path2_length = nx.shortest_path_length(
                self.graph, source=pickup, target=dropoff, weight='length'
            )
            return path1_length + path2_length
        except nx.NetworkXNoPath:
            return float('inf')
    ###--- [END: Search/Optimization] ---###

    ###--- [START: Search/Optimization & Automated Negotiation] ---###
    def _is_task_feasible(self, new_task_dropoff_location, depot_location, min_buffer_percent) -> bool:
        
        nodes_to_visit = list(set([p.dropoff_location for p in self.packages_on_board]))
        if new_task_dropoff_location not in nodes_to_visit:
            nodes_to_visit.append(new_task_dropoff_location)
        current_loc = self.location
        total_hypothetical_distance = 0.0

        while nodes_to_visit:
            closest_node = None
            shortest_dist = float('inf')
            for node in nodes_to_visit:
                try:
                    dist = nx.shortest_path_length(
                        self.graph, source=current_loc, target=node, weight='length'
                    )
                    if dist < shortest_dist:
                        shortest_dist = dist
                        closest_node = node
                except nx.NetworkXNoPath:
                    continue 
            if closest_node is None:
                return False 
            total_hypothetical_distance += shortest_dist
            current_loc = closest_node
            nodes_to_visit.remove(closest_node)

        try:
            dist_to_depot = nx.shortest_path_length(
                self.graph, source=current_loc, target=depot_location, weight='length'
            )
            total_hypothetical_distance += dist_to_depot
        except nx.NetworkXNoPath:
            return False 

        total_drain_needed = total_hypothetical_distance * self.drain_per_meter
        if self.current_battery < total_drain_needed:
            return False 
        
        return True 
    ###--- [END: Search/Optimization & Automated Negotiation] ---###

    ###--- [START: Interaction Protocols & Automated Negotiation] ---###
    def handle_cfp(self, task: dict) -> float:
        
        if self.status != 'available' or self.location != task['depot_location']:
            return None 
        if len(self.packages_on_board) >= self.capacity:
            return None
        
        pickup_location = task['pickup']
        dropoff_location = task['dropoff']
        try:
            depot_location = task['depot_location']
        except KeyError:
            print(f"[Agent {self.id}] ERROR: 'depot_location' not in task_info. Refusing bid.")
            return None
        
        is_feasible = self._is_task_feasible(
            dropoff_location, 
            depot_location, 
            self.min_working_buffer_percent
        )
        
        if not is_feasible:
            print(f"[Agent {self.id}] Reject task {task['id']}: Not enough battery for TOTAL trip.")
            return None
        
        travel_distance = self._calculate_travel_distance(pickup_location, dropoff_location)
        print(f"[Agent {self.id}] Submitting bid for Task {task['id']} with {travel_distance:.2f}m - (Holding {len(self.packages_on_board)} packages).")
        return travel_distance
    ###--- [END: Interaction Protocols & Automated Negotiation] ---###

    ###--- [START: Interaction Protocols & Search/Optimization] ---###
    def evaluate_bids(self, proposals: dict, task_object: Package):
        if not proposals:
            self.reject_proposal()
            return
            
        ###--- [START: Search/Optimization] ---###
        winner_agent = min(proposals, key=proposals.get)
        winning_bid = proposals[winner_agent]
        ###--- [END: Search/Optimization] ---###

        if winner_agent == self:
            print(f"Agent {self.id}: All bids reviewed. I am the most suitable for Task {task_object.id} with {winning_bid:.2f}m.")
            self.accept_proposal(task_object)
        else:
            print(f"Agent {self.id}: All bids reviewed. Agent {winner_agent.id} is the most suitable Agent forr Task {task_object.id} with {winning_bid:.2f}m.")
            self.reject_proposal()
    ###--- [END: Interaction Protocols & Search/Optimization] ---###
    
    def accept_proposal(self, task_object: Package):
        print(f"Agent {self.id}: Accept Task {task_object.id}! (Total: {len(self.packages_on_board) + 1} packages).")
        self.packages_on_board.append(task_object)
        task_object.assign(self) 
        
        if len(self.packages_on_board) >= self.capacity:
            print(f"Agent {self.id}: Capacity full! Planning route and departing.")
            ###--- [TRIGGER FOR: Search/Optimization] ---###
            self._plan_and_depart()
            ###--- [END TRIGGER] ---###
            
    ###--- [START: Search/Optimization] ---###
    def _plan_and_depart(self):
        self.status = 'busy'
        current_loc = self.location
        nodes_to_visit = list(set([p.dropoff_location for p in self.packages_on_board]))
        final_path = [] 
        self.dropoff_order = [] 
        total_route_distance = 0.0 

        print(f"Agent {self.id}: Planning route to {len(nodes_to_visit)} unique dropoffs...")

        while nodes_to_visit:
            closest_node = None
            shortest_dist = float('inf')
            
            for node in nodes_to_visit:
                try:
                    dist = nx.shortest_path_length(
                        self.graph, source=current_loc, target=node, weight='length'
                    )
                    if dist < shortest_dist:
                        shortest_dist = dist
                        closest_node = node
                except nx.NetworkXNoPath:
                    print(f"Agent {self.id}: Warning! No path to {node}, skipping.")
                    if node in nodes_to_visit: nodes_to_visit.remove(node)
                    continue
            
            if closest_node is None:
                break 

            total_route_distance += shortest_dist 
            
            path_segment = nx.shortest_path(
                self.graph, source=current_loc, target=closest_node, weight='length'
            )[1:]
            
            final_path.extend(path_segment)
            self.dropoff_order.append(closest_node)
            current_loc = closest_node
            if closest_node in nodes_to_visit: nodes_to_visit.remove(closest_node)

        depot_location = self.packages_on_board[0].pickup_location
        print(f"Agent {self.id}: All dropoffs planned. Returning to depot {depot_location}...")
        try:
            dist_to_depot = nx.shortest_path_length(
                self.graph, source=current_loc, target=depot_location, weight='length'
            )
            total_route_distance += dist_to_depot 
            
            path_to_depot = nx.shortest_path(
                self.graph, source=current_loc, target=depot_location, weight='length'
            )[1:]
            final_path.extend(path_to_depot)
        except nx.NetworkXNoPath:
             print(f"Agent {self.id}: Warning! No path back to depot.")
        
        self.path = final_path
        total_drain = total_route_distance * self.drain_per_meter
        print(f"Agent {self.id}: Route determined ({len(self.path)} nodes).")
        print(f"  > Total Distance: {total_route_distance:.2f}m. Est. Battery Drain: {total_drain:.1f} (Current: {self.current_battery:.1f})")
    ###--- [END: Search/Optimization] ---###

    def reject_proposal(self):
        pass 

    def move(self):
        if not self.path:
            print(f"Agent {self.id}: Finished route and returned to depot.")
            self.status = 'available'
            self.packages_on_board = []
            self.dropoff_order = []   
            return
        
        if self.current_battery <= 0:
            print(f"Agent {self.id}: Out of battery! Stop at {self.location}.")
            return

        current_loc = self.location
        next_node = self.path.pop(0) 
        try:
            distance_of_step = self.graph.edges[current_loc, next_node, 0]['length'] 
        except KeyError:
            print(f"Agent {self.id}: Error: Edge {current_loc}-{next_node} not found.")
            distance_of_step = 0 
        drain = distance_of_step * self.drain_per_meter
        self.current_battery -= drain
        self.location = next_node 
        if self.current_battery < 0:
            self.current_battery = 0
        
        if self.dropoff_order and self.location == self.dropoff_order[0]:
            node_delivered = self.dropoff_order.pop(0)
            print(f"Agent {self.id}: Arrived at dropoff {node_delivered}.")
            packages_remaining = []
            for pkg in self.packages_on_board:
                if pkg.dropoff_location == node_delivered:
                    pkg.complete()
                    print(f"Agent {self.id}: Delivered Package {pkg.id}.")
                else:
                    packages_remaining.append(pkg)
            self.packages_on_board = packages_remaining