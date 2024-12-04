import matplotlib.pyplot as plt
import numpy as np


def save_probability_map(grid_pm, grid_size, filename="probability_map.png"):
    if not isinstance(grid_pm, np.ndarray):
        grid_pm = np.array(grid_pm)

    # Reshape the grid_pm to a 2D array
    grid_pm = grid_pm.reshape((grid_size, grid_size))

    fig, ax = plt.subplots()

    cax = ax.matshow(grid_pm, cmap="Blues", vmin=0, vmax=1)

    fig.colorbar(cax)

    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")
    ax.set_title("Probability Map")

    plt.savefig(filename)
    plt.close()


arr = [
    0.94117647,
    0.5,
    0.64,
    0.8,
    0.1,
    0.1,
    0.04705882,
    0.01219512,
    0.8,
    0.30769231,
    0.04705882,
    0.30769231,
    0.94117647,
    0.30769231,
    0.1,
    0.94117647,
]
save_probability_map(arr, 4)
