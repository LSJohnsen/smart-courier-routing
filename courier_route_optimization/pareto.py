import csv
from datetime import datetime

"""
Functions for evaluating Pareto optimality of courier routes for time, cost, and CO2.
"""
#True if p=(time,cost,co2) is dominated by any point in others
def is_dominated(p, others):
    for q in others:
        if (q[0] <= p[0] and q[1] <= p[1] and q[2] <= p[2]) and (q != p): 
            return True
    return False

#index of non-dominated points
def pareto_index(points):
    non_dominated = []
    for i, p in enumerate(points):
        if not is_dominated(p, points[:i] + points[i+1:]):
            non_dominated.append(i)
    return non_dominated


def evaluate_pareto_routes(optimizer, n_steps=12, gammas=(0.2, 0.6, 1.0, 1.6), save_csv=True):
    performance, weights, routes, gammas_used = [], [], [], []
    seen = set()  # stop identical duplicate (route + gamma + weights)

    for gamma in gammas:            # for each different gamma value iterate over n steps of weight combinations
        for i in range(n_steps + 1):    #loop fixed by gpt - see report 
            for j in range(n_steps + 1 - i):
                k = n_steps - i - j
                if i + j + k == 0:
                    continue

                w_t, w_c, w_z = i / n_steps, j / n_steps, k / n_steps
                optimizer.multi_weights = {"time": w_t, "cost": w_c, "co2": w_z}

                order_time, order_co2, order_cost, order_multi = optimizer.closest_route_order(multiobj=True, prio_gamma=gamma)
                key = (tuple(order_multi), round(gamma, 6), round(w_t, 6), round(w_c, 6), round(w_z, 6))
                if key in seen:
                    continue
                seen.add(key)

                totals = optimizer.route_totals(order_multi, prio_on_time=False)
                performance.append((totals["t_actual"], totals["cost"], totals["co2"]))
                weights.append((w_t, w_c, w_z))
                routes.append(order_multi)
                gammas_used.append(gamma)

 
    non_dominated = set(pareto_index(performance))

    if save_csv:
        path = "pareto_results.csv"
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "gamma", "w_time", "w_cost", "w_co2",
                "time_h", "cost_NOK", "co2_g", "non_dominated"
            ])
            now = datetime.now().isoformat()
            for i, (t, c, z) in enumerate(performance):
                writer.writerow([
                    now, gammas_used[i],
                    *weights[i],
                    t, c, z,
                    "yes" if i in non_dominated else "no"
                ])
        print(f"Saved Pareto results to {path}")

    return {
        "performance": performance,
        "weights": weights,
        "routes": routes,
        "gammas": gammas_used
    }