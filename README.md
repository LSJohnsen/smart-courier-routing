# Smart Courier Routing

Smart Courier Routing is an optimization tool for delivery route planning created in accordance with the final project for ACIT4420.  
It determines the optimal delivery order for a courier service based on distance, delivery priority, and environmental or economic objectives.  

The system supports time, cost, CO₂, and multi-objective optimization, and can optionally generate Pareto fronts to analyze trade-offs between competing metrics.

---

## Features

- Optimize delivery routes by:
  - **Fastest delivery time**
  - **Lowest total cost**
  - **Lowest CO₂ emissions**
  - **Weighted multi-objective** combination
- Priority scaling for urgent deliveries
- Pareto optimization for exploring trade-offs
- Optional route plotting and CSV export
- Configurable weighting of objectives via CLI

---

## Installation (Local)

1. Clone or download this repository:
   ```bash
   git clone https://github.com/LSJohnsen/smart-courier-routing.git
   cd smart-courier-routing
   pip install -e .
   smart-courier --help
