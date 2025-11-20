import csv
import json
from pathlib import Path
import re

'''
Loads all the deliveries from csv file, checks if all required fields are there and in the correct formats and returns it 
as a dictionary for use in the optimizer 
returns list of the valid and invalid deliveries for logging & optimization
'''

def load_depot(json_path: Path):
    with open(json_path, 'r') as f:
        data = json.load(f)
        try:
            lat = float(data["latitude"])
            lon = float(data["longitude"])
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Depot coordinates are out of valid range")
            return {"name": "Depot", "lat": lat, "lon": lon}
        except Exception as e:
            raise ValueError(f"Invalid depot data: {e}")
  
def load_deliveries(csv_path: Path):
    deliveries = []
    rejected = []
    NAME_OK = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ'’\-\.\s]+$") # lower/upper( english, latin, scandinavian), apo, dash, dot, space
    
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        contents = {"customer", "latitude", "longitude", "priority", "weight_kg"}

        missing_columns = contents - set(reader.fieldnames or [])
        if missing_columns:
            raise ValueError(f"the required column(s): {missing_columns} is missing")

        for i, row in enumerate(reader, start=2):
            try:
                name = (row.get("customer") or "").strip()
                if not name:
                    raise ValueError("No customer name")
                if not NAME_OK.match(name):
                    raise ValueError("Invalid customer name (contains digits or illegal characters)")

                # prevent none, space, range, priority, weight 
                lat_str = (row.get("latitude") or "").strip().replace(",", ".") 
                lon_str = (row.get("longitude") or "").strip().replace(",", ".")
                lat = float(lat_str)
                lon = float(lon_str)
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError("Coordinates are out of valid range")

                
                priority = (row.get("priority") or "").strip().lower()
                if priority not in ("high", "medium", "low"):
                    raise ValueError("The priority value is not valid (high/medium/low)")

                
                weight = float((row.get("weight_kg") or "").strip().replace(",", "."))
                if weight <= 0:
                    raise ValueError("The package weight is zero or negative value")

                deliveries.append({
                    "customer": name,
                    "lat": lat,
                    "lon": lon,
                    "priority": priority,
                    "weight_kg": weight
                })

            except Exception as e:
                rejected.append({"row": i, "cause": str(e), **row}) #(**kwarg unpack key-value instead of just syntax error (fixed by gpt))

    return deliveries, rejected

# Writes csv with the rejected deliveries 
def rejected_deliveries(rejected, csv_path: Path):
    if not rejected:
        return
    
    fields = ["row", "cause", "customer", "latitude", "longitude", "priority", "weight_kg"]

    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rejected)
        
# Writes csv of the final route deliveries
def write_route_csv(rows, out_path: Path):
    fields = ["customer","latitude","longitude","distance_from_previous",
              "cumulative_distance","eta_from_start",
              "time_to_current","cost_to_current","co2_to_current"]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


#depot = load_depot(Path("Locations/depot.json"))
#deliveries, rejected = load_deliveries(Path("Locations/deliveries.csv"))
#print(rejected)