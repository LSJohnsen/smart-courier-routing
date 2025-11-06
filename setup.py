from setuptools import setup, find_packages

setup(
    name="smart-courier-routing",
    version="1.0.0",
    author="Lars Johnsen",
    author_email="s359056@oslomet.no",
    url="https://github.com/LSJohnsen/smart-courier-routing",
    description="Courier route optimization with time, cost, CO2, and Pareto sweep",
    packages=find_packages(include=["courier_route_optimization*", "SMART_COURIER*"]),
    python_requires=">=3.9",
    install_requires=[
        "matplotlib>=3.6",
    ],
    entry_points={
        "console_scripts": [
            "smart-courier=SMART_COURIER.main:main",
        ],
    },
    include_package_data=True,
)