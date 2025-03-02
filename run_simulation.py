import numpy as np
import random
import matplotlib.pyplot as plt
from collections import deque, defaultdict
import pygame
import argparse
from time import time

from model import Simulation

# Define the seating strategies to compare
seating_strategies = ['random', 'door_wise', 'window_wise', 'optimal']
num_runs = 10
results = {strategy: [] for strategy in seating_strategies}

# Function to run a single simulation for a given strategy and return time to finish
def run_simulation_for_strategy(strategy):
    # Reinitialize simulation with the specific seating strategy
    simulation = Simulation(
        seat_rows=5,  # Example parameters
        seat_in_row=[3, 3],
        door_choice='both',
        baggage_probability=0.6,
        ticks_per_second=5000,
        seating_strategy=strategy
    )
    time_to_finish, ticks, _ = simulation.run()
    return time_to_finish / 1000, ticks  # Convert to seconds

# Run the simulations for all strategies and store the results
for strategy in seating_strategies:
    for _ in range(num_runs):
        random.seed(_)  # Use different seeds for each run
        np.random.seed(_)  # Set the seed for reproducibility
        time_taken, ticks_taken = run_simulation_for_strategy(strategy)
        results[strategy].append(ticks_taken)

# Create a boxplot comparing the time taken for each seating strategy
plt.figure(figsize=(8, 6))
plt.boxplot(results.values(), tick_labels=seating_strategies)  # Update labels to tick_labels
plt.title("Comparison of Different Seating Strategies")
plt.ylabel("Game ticks")
plt.xlabel("Seating Strategy")
plt.grid(True)
plt.show()

