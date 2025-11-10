

from datetime import datetime, timedelta
from courier_route_optimization.constants import Mode, MODE_PARAMS, URGENCY_MULT, EARTH_RADIUS_KM
from courier_route_optimization.utils import normalize, haversine
import math



'''
Class that optimizes the courier route based on depot and deliveries location, delivery mode and objective
Applies cost function to determien the route order based on desired urgency weights by distance and a priorty exponent 
'''

class RouteOptimizer:
    def __init__(self, depot: dict, deliveries: list[dict], mode: Mode, objective: str, multi_weights: dict):
        self.depot = depot                  #name, lat, lon
        self.deliveries = deliveries        #customer, lon, lat, weight, prio
        self.mode = mode                    #car|walk|bicycle 
        self.objective = objective          #time|cost|co2
        self.multi_weights = multi_weights  # weights for multi-objective scoring

    # Returns the metrics for delivery time, cost and CO2 
    def _delivery_metrics(self, distance: float):
        d_mode = MODE_PARAMS[self.mode]     # gets "speed", "cost", and "co2" for the chosen delivery mode
        d_time = distance / d_mode["speed"] # km_distance / km/h 
        d_cost = distance * d_mode["cost"]  # nok/km
        d_co2 = distance * d_mode["co2"]    #  g/km 
        
        return d_time, d_cost, d_co2

    # Determines the clostest delivery points by km and weights 
    def closest_route_order(self, multiobj=False, prio_gamma=0.6):
        
        order_time = []                                             # List of deliveris determined by time objective
        remaining_deliveries = set(range(len(self.deliveries)))     # set of remaining objectives
        cur_lat, cur_lon = self.depot["lat"], self.depot["lon"]     # Coordinates start

        
        while remaining_deliveries:
            # determine distances for all the remaining objectives
            distances = {
                k: haversine(cur_lat, cur_lon, self.deliveries[k]["lat"], self.deliveries[k]["lon"]) for k in remaining_deliveries}
            d_max = max(distances.values()) or 0.0001  # avoid zero div

            # function to compute the keys for remaining deliveries by time and priority based on a scaling distance function, increased gamma -> more priority weight on distant points
            def key_time(k: int) -> float:
                d = distances[k]
                d_norm = d / d_max
                base_prio = URGENCY_MULT[self.deliveries[k]["priority"]]         # priority weight high/med/low
                prio_dyn = base_prio ** (1.0 + prio_gamma * d_norm)              # dynamic priority -> priority ** (1+gamma*normalized distance) 
                return prio_dyn * d                                              

             # index next delivery, append, update position and remove the finished delivery from list
            j_time = min(remaining_deliveries, key=key_time)           
            order_time.append(j_time)
            cur_lat, cur_lon = self.deliveries[j_time]["lat"], self.deliveries[j_time]["lon"]
            remaining_deliveries.remove(j_time)



        
        # co2 same logic, but no scaling priority
        order_co2 = []
        remaining_deliveries_co2 = set(range(len(self.deliveries)))
        cur_lat_co2, cur_lon_co2 = self.depot["lat"], self.depot["lon"]
        co2_per_km = MODE_PARAMS[self.mode]["co2"]

        while remaining_deliveries_co2:
            j_co2 = min(remaining_deliveries_co2,
                key=lambda k: co2_per_km * haversine(cur_lat_co2, cur_lon_co2, self.deliveries[k]["lat"], self.deliveries[k]["lon"]))
            order_co2.append(j_co2)
            cur_lat_co2, cur_lon_co2 = self.deliveries[j_co2]["lat"], self.deliveries[j_co2]["lon"]
            remaining_deliveries_co2.remove(j_co2)


        # cost, same as co2 
        order_cost = []
        remaining_deliveries_cost = set(range(len(self.deliveries)))
        cur_lat_cost, cur_lon_cost = self.depot["lat"], self.depot["lon"]
        cost_per_km = MODE_PARAMS[self.mode]["cost"]

        while remaining_deliveries_cost:
            j_cost = min(remaining_deliveries_cost,
                key=lambda k: cost_per_km * haversine(cur_lat_cost, cur_lon_cost, self.deliveries[k]["lat"], self.deliveries[k]["lon"]))
            
            order_cost.append(j_cost)
            cur_lat_cost, cur_lon_cost = self.deliveries[j_cost]["lat"], self.deliveries[j_cost]["lon"]
            remaining_deliveries_cost.remove(j_cost)

        '''
        multi-objective optimization by weighted sum of time, cost and co2 (Currently only dynamic priority on time as the other metrics got no other scaling factors)
        Follows similar logic but also applies a weight for each metric based on wanted importance, which can be optimized by pareto front 
        '''
        order_multi = []
        if multiobj:
            remaining_deliveries_m = set(range(len(self.deliveries)))
            cur_lat_m, cur_lon_m = self.depot["lat"], self.depot["lon"]

            # weights for each metric
            w = self.multi_weights  
            w_time = w["time"] 
            w_cost = w["cost"] 
            w_co2 = w["co2"]
            
            # get paremeters based on the chosen mode car/bicycle/walk
            speed = MODE_PARAMS[self.mode]["speed"]
            cost_per_km = MODE_PARAMS[self.mode]["cost"]
            co2_per_km  = MODE_PARAMS[self.mode]["co2"]

            while remaining_deliveries_m:
                
                distances = {
                    k: haversine(cur_lat_m, cur_lon_m,
                                self.deliveries[k]["lat"], self.deliveries[k]["lon"])
                    for k in remaining_deliveries_m}

                
                d_max = max(distances.values()) or 0.0001
                # get keys for each remaining delivery based on weighted sum of time, cost and co2. also uses the priority scaling for the time metric. 
                def key_multi(k: int) -> float:
                    distance = distances[k]
                    d_time, d_cost, d_co2 = self._delivery_metrics(distance)
                    d_norm = distance / d_max
                    base_prio = URGENCY_MULT[self.deliveries[k]["priority"]]
                    prio_dyn = base_prio ** (1.0 + prio_gamma * d_norm)
                 
                    return w_time * prio_dyn * d_time + w_cost * d_cost + w_co2 * d_co2 # determine the actual metrics and apply weights

                j_multi = min(remaining_deliveries_m, key=key_multi)
                order_multi.append(j_multi)
                cur_lat_m, cur_lon_m = self.deliveries[j_multi]["lat"], self.deliveries[j_multi]["lon"]
                remaining_deliveries_m.remove(j_multi)

        
        return order_time, order_co2, order_cost, order_multi


    '''
    Method to calculate raw metrics of the route based on the delivery order
    '''
    def route_totals(self, order: list[int], prio_on_time = True) -> dict[str, float]:
        """
        Returns base totals independent of chosen objective:
        - time: priority-weighted total time (if prio_on_time=True)
        - cost: total cost
        - co2:  total CO2
        - t_actual: unweighted travel time 
        """
        t_sum = 0.0
        cost_sum = 0.0
        co2_sum = 0.0
        t_actual = 0.0

        # depot -> first
        first = self.deliveries[order[0]]
        dist = haversine(self.depot["lat"], self.depot["lon"], first["lat"], first["lon"])
        
        d_time, d_cost, d_co2 = self._delivery_metrics(dist)
        w_prio = URGENCY_MULT[first["priority"]] if prio_on_time else 1.0
        t_sum += w_prio * d_time
        cost_sum += d_cost
        co2_sum += d_co2
        t_actual += d_time

        # loop through deliveries by delivery order 
        for i in range(1, len(order)):
            # determine distance from previous to current stop and determine metrics 
            a = self.deliveries[order[i-1]]     
            b = self.deliveries[order[i]]
            dist = haversine(a["lat"], a["lon"], b["lat"], b["lon"])
            d_time, d_cost, d_co2 = self._delivery_metrics(dist)

            # add metrics to the totals 
            w_prio = URGENCY_MULT[b["priority"]] if prio_on_time else 1.0
            t_sum += w_prio * d_time
            cost_sum += d_cost
            co2_sum += d_co2
            t_actual += d_time

        # return to depot (no priority on return)
        last = self.deliveries[order[-1]]
        dist = haversine(last["lat"], last["lon"], self.depot["lat"], self.depot["lon"])
        d_time, d_cost, d_co2 = self._delivery_metrics(dist)
        t_sum += d_time
        cost_sum += d_cost
        co2_sum += d_co2
        t_actual += d_time

        return {"time": t_sum, "cost": cost_sum, "co2": co2_sum, "t_actual": t_actual}
            
    '''
    Follows same logic as route_scores but builds route with the wanted outputs format
    '''

    def route_scores(self, order: list[int]) -> tuple[float, float]:
        '''
        Calculates the total route score using per-metric normalization:
        where refs are computed inline from a simple star baseline.
        '''
        totals = self.route_totals(order, prio_on_time=True)

    
        depot_lat, depot_lon = self.depot["lat"], self.depot["lon"]
        speed = MODE_PARAMS[self.mode]["speed"]
        cost_per_km = MODE_PARAMS[self.mode]["cost"]
        co2_per_km  = MODE_PARAMS[self.mode]["co2"]

        time_ref = 0.0
        cost_ref = 0.0
        co2_ref  = 0.0

        # Loops over every delivery point and find the distance to each point and back (2*distance) where time is weighted by priority 
        for d in self.deliveries:
            dist = haversine(depot_lat, depot_lon, d["lat"], d["lon"])
            prio = URGENCY_MULT[d["priority"]]
       
            cost_ref += 2.0 * dist * cost_per_km
            co2_ref  += 2.0 * dist * co2_per_km
            time_ref += prio * (dist / speed) + (dist / speed)

        # find the max 
        zero_div = 0.0001
        refs = {
            "time": max(time_ref, zero_div),
            "cost": max(cost_ref, zero_div),
            "co2":  max(co2_ref,  zero_div),
        }

        # normalize between [0,1] based on the max values for equal scoring
        scores = {
            "time": normalize(totals["time"] / refs["time"]),
            "cost": normalize(totals["cost"] / refs["cost"]),
            "co2":  normalize(totals["co2"]  / refs["co2"]),
        }

        # do per objective weight if doing multi-optimization 
        if self.objective == "multi":
            w = self.multi_weights  
            total_score = (
                w["time"] * scores["time"] +
                w["cost"] * scores["cost"] +
                w["co2"]  * scores["co2"]
            )
        else:
            total_score = scores[self.objective]

        return total_score, totals["t_actual"]
        
    # Build the route for plotting and logging - same logic as route_totals
    def route_builder(self, order, start_time):
        route = []
        cum_dis = 0.0
        cum_time = 0.0

        # Method to add stop to the route list
        def add_stop(customer, lat, lon, distance, time, cost, co2):
            nonlocal cum_dis, cum_time
            cum_dis += distance
            cum_time += time
            time_arrival = start_time + timedelta(hours=cum_time)

            route.append({"customer": customer,
                          "latitude": f"{lat:.6f}",
                          "longitude": f"{lon:.6f}",
                          "distance_from_previous": distance,
                          "cumulative_distance": cum_dis,
                          "eta_from_start": time_arrival.isoformat(timespec="minutes"),
                          "time_to_current": f"{time:.2f}",
                          "cost_to_current": f"{cost:.2f}",
                          "co2_to_current": f"{co2:.2f}"
                          })

        # Initilize from depot to first
        add_stop(self.depot["name"], self.depot["lat"], self.depot["lon"], 0, 0, 0, 0)

        #depot to first
        first = self.deliveries[order[0]]
        distance = haversine(self.depot["lat"], self.depot["lon"], first["lat"], first["lon"])

        # loop through deliveries
        for i in range(1, len(order)):
            a = self.deliveries[order[i-1]]  
            b = self.deliveries[order[i]]
            distance = haversine(a["lat"], a["lon"], b["lat"], b["lon"])

            d_time, d_cost, d_co2 = self._delivery_metrics(distance)
            add_stop(b["customer"], b["lat"], b["lon"], distance, d_time, d_cost, d_co2)
            
        # return
        last = self.deliveries[order[-1]]
        distance = haversine(last["lat"], last["lon"], self.depot["lat"], self.depot["lon"])
        d_time, d_cost, d_co2 = self._delivery_metrics(distance)
        add_stop(self.depot["name"], self.depot["lat"], self.depot["lon"], distance, d_time, d_cost, d_co2)

        return route


        