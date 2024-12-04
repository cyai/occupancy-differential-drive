import numpy as np
from prettytable import PrettyTable


class OccupancyGrid:
    def __init__(self, grid_size, state_directions, p_free, p_occupied):
        self.grid_size = grid_size
        self.state_directions = state_directions
        # self.z_t = z_t
        self.p_free = p_free
        self.p_occupied = p_occupied
        self.grid = np.zeros((grid_size**2, len(state_directions) + 1))
        self.l_0 = 0
        self.pm = np.full((self.grid_size**2,), 0.5)

    def calculate_log_odds_free(self, p_free: float) -> float:
        """Calculates log-odds for free cells."""
        return np.log(p_free / (1 - p_free))

    def calculate_log_odds_occupied(self, p_occupied: float) -> float:
        """Calculates log-odds for occupied cells."""
        return np.log(p_occupied / (1 - p_occupied))

    def calculate_log_odds_unknown(self, p_unknown: float) -> float:
        """Calculates log-odds for unknown cells."""
        return np.log(p_unknown / (1 - p_unknown))

    def grid_col_row_to_index(self, row: int, col: int) -> int:
        """Converts grid row and column to 1D index."""
        return row * self.grid_size + col

    def calculate_li(
        self, state: int, direction: str, range_: int, previous_li: list, t: int
    ) -> list[int]:
        """Calculates neighbors within sensor range based on direction."""
        li = previous_li.copy()

        row, col = divmod(state, self.grid_size)
        for _ in range(1, range_ + 1):
            if direction == "R" and col + 1 < self.grid_size:
                index = self.grid_col_row_to_index(row, col + 1)
                li[index] += self.calculate_log_odds_free(self.p_free)
                col = col + 1
            elif direction == "U" and row - 1 >= 0:
                index = self.grid_col_row_to_index(row - 1, col)
                li[index] += self.calculate_log_odds_free(self.p_free)
                row = row - 1
            elif direction == "L" and col - 1 >= 0:
                index = self.grid_col_row_to_index(row, col - 1)
                li[index] += self.calculate_log_odds_free(self.p_free)
                col = col - 1
            elif direction == "D" and row + 1 < self.grid_size:
                index = self.grid_col_row_to_index(row + 1, col)
                li[index] += self.calculate_log_odds_free(self.p_free)
                row = row + 1
        for _ in range(range_, self.grid_size - range_):
            if direction == "D" and row + 1 <= self.grid_size:
                index = self.grid_col_row_to_index(row + 1, col)
                if index < len(li):
                    li[index] += self.calculate_log_odds_occupied(self.p_occupied)

                row = row + 1

            elif direction == "R" and col + 1 < self.grid_size:
                index = self.grid_col_row_to_index(row, col + 1)
                if index < len(li):
                    li[index] += self.calculate_log_odds_occupied(self.p_occupied)

                col = col + 1
            elif direction == "U" and row - 1 >= 0:
                index = self.grid_col_row_to_index(row - 1, col)
                if index >= 0:
                    li[index] += self.calculate_log_odds_occupied(self.p_occupied)

                row = row - 1
            elif direction == "L" and col - 1 >= 0:
                index = self.grid_col_row_to_index(row, col - 1)
                if index >= 0:
                    li[index] += self.calculate_log_odds_occupied(self.p_occupied)
                col = col - 1

        return li

    def update_grid_with_robot_observations(self, z_t: list) -> np.ndarray:
        """Updates grid with robot observations."""
        previous_li = [0] * self.grid_size**2
        li = [0] * self.grid_size**2
        for t, (state, direction) in enumerate(self.state_directions, start=1):
            row, col = state
            state_index = self.grid_col_row_to_index(row, col)
            range = z_t[t - 1] if z_t[t - 1] >= 1 else 0
            li = self.calculate_li(state_index, direction, range, previous_li, t - 1)
            previous_li = li

            self.grid[:, t] = li

    def update_individual_grid_column(
        self, t: int, state: tuple, direction: str, range_: int, initial: bool = False
    ) -> None:
        """Updates individual grid column."""
        row, col = state
        if initial:
            previous_li = [0] * self.grid_size**2
        else:
            previous_li = self.grid[:, t - 1]
        state_index = self.grid_col_row_to_index(row, col)
        li = self.calculate_li(state_index, direction, range_, previous_li, t - 1)
        print(
            f"State: {state}, Direction: {direction}, Range: {range_}, state_index: {state_index}"
        )
        print(f"Li: {li}")
        print(f"----x------x------x-----\n")
        previous_li = li

        self.grid[:, t] = li

    def calculate_pm(self) -> float:
        last_column = self.grid[:, -2]
        for i in range(self.grid_size**2):
            self.pm[i] = (
                np.exp(last_column[i]) / (1 + np.exp(last_column[i]))
                if last_column[i] != 0
                else 0.5
            )

        return self.pm

    def display_grid(self):
        """Displays the grid map using PrettyTable."""
        table = PrettyTable()
        table.field_names = [
            "Cell",
            *range(1, len(self.state_directions) + 2),
        ]
        for i in range(self.grid_size**2):
            table.add_row([i + 1, *self.grid[i]])

        with open("grid.txt", "w") as f:
            f.writelines("Occupancy Grid\n")
            f.write(str(table))
        print(table)


if __name__ == "__main__":
    GRID_SIZE = 5
    STATE_DIRECTIONS = [
        ((4, 0), "R"),
        ((4, 1), "U"),
        ((4, 2), "U"),  # Cell 1, Right
        ((4, 3), "U"),  # Cell 2, Down
        ((3, 3), "L"),  # Cell 5, Down
    ]
    Z_T = [3, 0.1, 1, 1, 1]  # Example sensor readings
    P_FREE = 0.1
    P_OCCUPIED = 0.8
    # GRID_SIZE = 3
    # STATE_DIRECTIONS = [
    #     ((2, 0), "U"),  # Cell 7, Up
    #     ((1, 0), "U"),  # Cell 4, Up
    #     ((0, 0), "R"),  # Cell 1, Right
    #     ((0, 1), "D"),  # Cell 2, Down
    #     ((1, 1), "D"),  # Cell 5, Down
    #     ((1, 1), "R"),  # Cell 5, Right
    #     ((1, 2), "D"),  # Cell 6, Down
    #     ((1, 2), "U"),  # Cell 6, Up
    #     ((1, 2), "L"),  # Cell 6, Left
    #     ((1, 1), "D"),  # Cell 5, Down
    # ]
    # Z_T = [2, 1, 1, 1, 0.1, 1, 0.1, 0.1, 2, 0.1]  # Example sensor readings
    # P_FREE = 0.2
    # P_OCCUPIED = 0.8

    grid = OccupancyGrid(GRID_SIZE, STATE_DIRECTIONS, P_FREE, P_OCCUPIED)
    grid.update_grid_with_robot_observations(Z_T)
    grid.display_grid()
