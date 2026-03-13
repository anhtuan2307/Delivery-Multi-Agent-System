# Intelligent Delivery Multi-Agent System (VRP Solver)
*Academic Project - Swinburne University of Technology COS30018 Intelligent Systems*

##  Project Overview
This project builds a decentralized model to solve the dynamic Vehicle Routing Problem. Autonomous agents negotiate for tasks and manage their own physical constraints in a simulated real-world environment.

##  Key Technical Features
- **Decentralized Decision Making:** Uses an adapted Contract Net Protocol. The Master Agent broadcasts tasks, while Delivery Agents bid competitively based on their local state.

- **Real-World Map Integration:** Operates on a street network graph of Cau Giay District (retrieved via OSMnx), utilizing Dijkstra's algorithm to calculate precise travel costs on actual roads.

- **Autonomous Constraint Management:**
  - **Proactive Battery Logic:** Agents simulate hypothetical routes using Greedy TSP to verify battery sufficiency before accepting any bid.
  - **Capacity Enforcement:** Agents strictly follow a physical cargo limit of 5 packages using batch processing.
  - **Anti-Livelock Mechanism:** Agents can intelligently trigger early departures if pending tasks exceed their current capabilities, completely preventing system deadlocks.

- **Distributed Optimization:** Each agent locally solves the Traveling Salesperson Problem using a Greedy Nearest Neighbor heuristic to optimize its specific delivery sequence.

##  System Architecture
- **Master Agent:** Manages the global task queue and acts as the auctioneer.
- **Delivery Agents:** Autonomous contractors that handle bidding, route planning, and real-time state transitions (Available, Busy, Recharging).

##  Technology Stack
- **Core:** Python 3.10+
- **Mapping & Routing:** OSMnx, NetworkX
- **Visualization:** Matplotlib

---
*Developed by: Doan Phuong Anh Tuan*
