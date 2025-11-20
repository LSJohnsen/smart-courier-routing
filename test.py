import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from courier_route_optimization.constants import Mode
from courier_route_optimization.IO.reader import load_deliveries, rejected_deliveries, load_depot, write_route_csv
from courier_route_optimization.utils import timer
from courier_route_optimization.route_optimizer import RouteOptimizer

# just for testing functionality outside main
@timer
def run(depot, deliveries, mode, objective, start=None, output="route.csv"):
    optimizer = RouteOptimizer(depot, deliveries, mode, objective)
    order = optimizer.closest_route_order()
    score, t_actual = optimizer.route_scores(order[0])
    start_time = datetime.fromisoformat(start) if start else datetime.now()
    rows = optimizer.route_builder(order[0], start_time)
    write_route_csv(rows, Path(output))
    return score, t_actual, order, rows

depot = load_depot(Path("Locations/depot.json"))
deliveries, rejected = load_deliveries(Path("Locations/deliveries.csv"))
rejected_deliveries(rejected, Path("Locations/rejected_deliveries.csv"))

if not deliveries:
    print("No valid deliveries. Exiting.")
    sys.exit(0)

    # Optimize and save determined route 
score, t_actual, order, rows = run(depot, deliveries, Mode.CAR, "time")

print(order)