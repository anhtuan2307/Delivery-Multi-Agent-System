# main_agent.py

import random
import networkx as nx
from delivery_agent import DeliveryAgent
from package import Package

class MainAgent:
    def __init__(self, graph: nx.Graph):
        self.graph = graph
        self.agents: list[DeliveryAgent] = [] 
        self.location = random.choice(list(graph.nodes))
        self.pending_tasks: list[Package] = [] 
        print(f"Main Agent (Depot) at node {self.location}")

    def create_agents(self, num_agents: int, buffer_percent: float):
        for i in range(num_agents):
            agent = DeliveryAgent(
                agent_id=i+1, 
                graph=self.graph, 
                min_working_buffer_percent=buffer_percent,
                start_node=self.location # Start at depot for capacity logic
            )
            self.agents.append(agent)

    def add_tasks(self, tasks: list[Package]):
        self.pending_tasks.extend(tasks)
        print(f"--- [Main Agent]: There are {len(tasks)} new packages. Total number of packages waiting: {len(self.pending_tasks)}. ---")
    
    def check_and_assign_tasks(self):
        if self.pending_tasks and any(agent.status == 'available' for agent in self.agents):
            task_to_assign = self.pending_tasks.pop(0) 
            
            ###--- [START: Interaction Protocols] ---###
            # Initiate the Contract Net Protocol
            self.initiate_contract_net(task_to_assign)
            ###--- [END: Interaction Protocols] ---###

    ###--- [START: Interaction Protocols] ---###
    # This function defines the "Call for Proposal" (CFP) phase
    def initiate_contract_net(self, task_object: Package):
        print(f"\n--- [Main Agent] Start Bidding for Task {task_object.id} (to node {task_object.dropoff_location}) ---")
        
        task_info = {
            'id': task_object.id,
            'pickup': task_object.pickup_location,
            'dropoff': task_object.dropoff_location,
            'depot_location': self.location
        }

        if not nx.has_path(self.graph, task_info['pickup'], task_info['dropoff']):
            print(f"--- [Main Agent] ERROR: No path found for Task {task_info['id']}. Cancelling task. ---")
            task_object.status = 'cancelled' 
            return
        
        proposals = {}
        print("--- [Main Agent] Send notice (CFP) to agents... ---")
        
        # Step 1: Send CFP to all agents and collect bids
        for agent in self.agents:
            bid = agent.handle_cfp(task_info) 
            
            if bid is not None:
                proposals[agent] = bid 

        ###--- [START: Automated Negotiation] ---###
        # Handle the result of the negotiation (bidding)
        
        # Case 1: Negotiation Fails (No bids received)
        if not proposals:
            print("--- [Main Agent] None available agents. Put the task back in the queue.--- ")
            self.pending_tasks.append(task_object) 
            return
        ###--- [END: Automated Negotiation] ---###

        print(f"--- [Main Agent] Received {len(proposals)} proposals. Sending bid list back to agents... ---")
        
        # Step 2: Send all proposals back to agents for
        # decentralized decision-making (part of this protocol)
        for agent_who_bid in proposals:
            agent_who_bid.evaluate_bids(proposals, task_object)
            
    ###--- [END: Interaction Protocols] ---###