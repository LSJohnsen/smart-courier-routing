

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path
from courier_route_optimization.constants import Mode
from courier_route_optimization.IO.reader import load_deliveries, rejected_deliveries, load_depot, write_route_csv
from courier_route_optimization.utils import timer
from courier_route_optimization.route_optimizer import RouteOptimizer
from courier_route_optimization.plots.plots import plot_route
from courier_route_optimization.pareto import evaluate_pareto_routes, get_pareto_indices

'''
Main script to run the route optimization with command line arguments:
specify CLI: main.py --deliveries Locations/deliveries.csv --depot Locations/depot.json --mode car/bicycle/walk --objective time/cost/co2 --plot --pareto
                Weigts can also be changed by --w-time 1.0... etc, but are defaulted to multi_weights dict values.

When running, pareto optimization evaluates multiple time gamma, and different weight combinations for time, cost, and CO2. 
Outputs the optimized route to a CSV file and optionally plots the route and Pareto front.
To run optimal routes in multi-objective apply one of the non-dominated solutions by changing the gamma and weights. 
'''

# optimizer.closest_route_order() index:
    # 0: time
    # 1: co2
    # 2: cost
    # 3: multi-objective


multi_weights = {"time": 0.9167,     # Weights for multi-objective scoring
                "cost": 0.0833, 
                "co2": 0.5896}
prio_gamma = 0.2                  # exponent weight for priority in choosing next point by priority_weight^(1+gamma*normalized_distance_to_point)


def main():
    # Take arguments from command line, optimizes and times entire optimization process
    @timer
    def run(depot, deliveries, args):                                                       
        optimizer = RouteOptimizer(
        depot, deliveries, args.mode, args.objective,
        {"time": args.w_time, "cost": args.w_cost, "co2": args.w_co2})

        # Compute all route orders
        o_time, o_co2, o_cost, o_multi = optimizer.closest_route_order(multiobj=True, prio_gamma=prio_gamma)
        orders = {"time": o_time, "cost": o_cost, "co2": o_co2, "multi": o_multi}

        # Choose which order type to actually build/score for this run 
        chosen = orders.get(getattr(args, "order_by", args.objective), o_time)

        # Compute total score and actual delivery time for chosen order 
        score, t_actual = optimizer.route_scores(chosen)

        # build and save the chosen route
        start_time = datetime.fromisoformat(args.start) if args.start else datetime.now()
        rows = optimizer.route_builder(chosen, start_time)
        write_route_csv(rows, Path(args.output))

        return score, t_actual, rows

    ap = argparse.ArgumentParser("Smart Courier Delivery Route Optimizer")
    ap.add_argument("--deliveries", required=True, help="deliveries CSV path")
    ap.add_argument("--depot", required=True, help="depot JSON path")
    ap.add_argument("--mode", required=True, choices=["car","bicycle","walk"])
    ap.add_argument("--objective", default="time", choices=["time","cost","co2","multi"], help="metric used for scoring")
    ap.add_argument("--order-by", default="time", choices=["time","cost","co2","multi"], help="which parameter to optimize when building the route")
    ap.add_argument("--w-time", type=float, default=multi_weights["time"], help="weight for time in multi-objective") # weights default to dict values
    ap.add_argument("--w-cost", type=float, default=multi_weights["cost"], help="weight for cost in multi-objective")
    ap.add_argument("--w-co2",  type=float, default=multi_weights["co2"], help="weight for CO2 in multi-objective")
    ap.add_argument("--output", default="route.csv")
    ap.add_argument("--rejected", default="rejected.csv")
    ap.add_argument("--start", default=None, help="ISO time; default now")
    ap.add_argument("--plot", action="store_true", help="Plot the optimized route and/or score comparison")
    ap.add_argument("--pareto", action="store_true", help="multi-objective weights and show Pareto front")
    ap.add_argument("--pareto-steps", type=int, default=12, help="Grid resolution for Pareto sweep")
    args = ap.parse_args()

 
    

    # Load data
    depot = load_depot(Path(args.depot))                            
    deliveries, rejected = load_deliveries(Path(args.deliveries))        
    rejected_deliveries(rejected, Path(args.rejected))
    if not deliveries:
        print("No valid deliveries. Exiting.")
        return

    # Run optimization and save
    score, t_actual, rows = run(depot, deliveries, args)
  
    
    # Console summary
    total_km  = sum(float(r["distance_from_previous"]) for r in rows if r["distance_from_previous"] != "0.000")
    total_h   = sum(float(r["time_to_current"]) for r in rows)
    total_nok = sum(float(r["cost_to_current"]) for r in rows)
    total_co2 = sum(float(r["co2_to_current"])  for r in rows)

    print(f"Mode: {args.mode} | Objective: {args.objective}")
    print(f"Stops (incl. depot rows): {len(rows)}")
    print(f"Distance: {total_km:.2f} km | Time: {total_h:.2f} h | Cost: {total_nok:.2f} NOK | CO2: {total_co2:.0f} g")
    print(f"Objective score ({args.objective}): {score:.3f} | Actual travel time: {t_actual:.3f} h")
    print(f"Saved {args.output}" + (f"; rejected rows saved in {args.rejected}" if rejected else ""))
    

    # Plotting
    if getattr(args, "pareto", False):
        # do optimizer and run pareto optim with different weights from args
        pareto_opt = RouteOptimizer(
            depot, deliveries, args.mode, "multi",
            {"time": args.w_time, "cost": args.w_cost, "co2": args.w_co2}
        )

        pareto_result = evaluate_pareto_routes(pareto_opt, n_steps=args.pareto_steps, gammas=(0.2, 0.6, 1.0, 1.6))
        non_dominated = get_pareto_indices(pareto_result["performance"])
        print(f"Pareto sweep: candidates={len(pareto_result['performance'])}, non-dominated={len(non_dominated)}")


    if args.plot:
        plot_route(args.output, save=True)
        

if __name__ == "__main__":
    main()