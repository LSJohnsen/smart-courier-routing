import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import pandas as pd
from pathlib import Path
from mpl_toolkits.basemap import Basemap

#https://gis.stackexchange.com/questions/364584/how-to-make-graphs-of-latitude-and-longitude-and-generating-summary-table

def plot_route(path, save=False, res='h'):

    route = pd.read_csv(Path(path))

    lat = route['latitude'].values
    lon = route['longitude'].values

    pad = 0.002  # smaller for closer zoom
    llcrnrlat, urcrnrlat = lat.min() - pad, lat.max() + pad
    llcrnrlon, urcrnrlon = lon.min() - pad, lon.max() + pad # zoom of map fixed by gpt


    fig = plt.figure(figsize=(10, 8))
    m = Basemap(projection="merc", resolution=res,
                llcrnrlat=llcrnrlat, urcrnrlat=urcrnrlat,
                llcrnrlon=llcrnrlon, urcrnrlon=urcrnrlon)

    # Draw base features
    m.drawcoastlines()
    m.drawcountries()
    m.drawmapboundary(fill_color="lightblue")
    m.fillcontinents(color="beige", lake_color="lightblue")
    m.drawparallels(range(int(llcrnrlat), int(urcrnrlat) + 1, 1), labels=[1,0,0,0])
    m.drawmeridians(range(int(llcrnrlon), int(urcrnrlon) + 1, 1), labels=[0,0,0,1])

    # Plot delivery points (gpt to add dots to each delivery point)
    x, y = m(lon, lat)

    m.plot(lon, lat, latlon=True, color="darkred", linewidth=2, zorder=4)
    m.scatter(lon, lat, latlon=True, c="red", s=70, edgecolors="black", linewidth=0.7, zorder=5)

    for i, (xx, yy) in enumerate(zip(x, y), start=1):
    
        label = "1" if i == len(x) else str(i)
        
        plt.text(
            xx, yy + 300, label,
            fontsize=10, fontweight="bold", color="black",
            ha="center", va="center", zorder=6,
            path_effects=[path_effects.withStroke(linewidth=3, foreground="white")]
        )

    plt.title("Optimized Delivery Route (Oslo area)")
    plt.show()

    if save:
    
        fig.savefig(
                "optimized_route.eps",
                format="eps",
                bbox_inches='tight',   
                pad_inches=0.05,       
                dpi=300                
            )
        plt.close(fig)             


# not used, gpt generated for testing some plotting
def plot_pareto(performance, pareto_indices, show_3d=False, save=False):
    """Plot 2D projections (and optional 3D) of the Pareto front."""
    performance = np.array(performance)
    time_vals, cost_vals, co2_vals = performance[:, 0], performance[:, 1], performance[:, 2]
    dominated = [i for i in range(len(performance)) if i not in pareto_indices]

    # Time vs Cost
    plt.figure()
    plt.scatter(time_vals[dominated], cost_vals[dominated],
                marker='o', facecolors='none', edgecolors='gray', label='Dominated')
    plt.scatter(time_vals[pareto_indices], cost_vals[pareto_indices],
                marker='o', color='blue', label='Pareto')
    plt.xlabel('Delivery Time (h)')
    plt.ylabel('Cost (NOK)')
    plt.title('Pareto Front: Time vs Cost')
    plt.legend()
    plt.grid(True)

    # Time vs CO₂
    plt.figure()
    plt.scatter(time_vals[dominated], co2_vals[dominated],
                marker='o', facecolors='none', edgecolors='gray', label='Dominated')
    plt.scatter(time_vals[pareto_indices], co2_vals[pareto_indices],
                marker='o', color='green', label='Pareto')
    plt.xlabel('Delivery Time (h)')
    plt.ylabel('CO₂ (g)')
    plt.title('Pareto Front: Time vs CO₂')
    plt.legend()
    plt.grid(True)

    # Cost vs CO₂
    plt.figure()
    plt.scatter(cost_vals[dominated], co2_vals[dominated],
                marker='o', facecolors='none', edgecolors='gray', label='Dominated')
    plt.scatter(cost_vals[pareto_indices], co2_vals[pareto_indices],
                marker='o', color='red', label='Pareto')
    plt.xlabel('Cost (NOK)')
    plt.ylabel('CO₂ (g)')
    plt.title('Pareto Front: Cost vs CO₂')
    plt.legend()
    plt.grid(True)

    # Optional 3D
    if show_3d:
        from mpl_toolkits.mplot3d import Axes3D  # noqa
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(time_vals[dominated], cost_vals[dominated], co2_vals[dominated],
                   facecolors='none', edgecolors='gray', label='Dominated')
        ax.scatter(time_vals[pareto_indices], cost_vals[pareto_indices], co2_vals[pareto_indices],
                   color='blue', label='Pareto Optimal')
        ax.set_xlabel('Time (h)')
        ax.set_ylabel('Cost (NOK)')
        ax.set_zlabel('CO₂ (g)')
        ax.set_title('3D Pareto Front')
        plt.legend()

    plt.show()
    if save == True:
        fig.savefig("Pareto_view.eps", format="eps")