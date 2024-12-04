from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pynput import keyboard
import threading
import json

from build_occupancy_grid import OccupancyGrid

COMMANDS = {
    "s": "MOVE_FORWARD",
    "w": "MOVE_BACKWARD",
    "d": "TURN_LEFT",
    "a": "TURN_RIGHT",
    "c": "STOP",
}

app = FastAPI()
websocket_client = None
calculate_ = False

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
GRID_SIZE = 4
STATE_DIRECTIONS = [
    ((2, 0), "U"),
    ((1, 0), "R"),
    ((0, 3), "D"),
    ((3, 2), "U"),
    ((3, 1), "R"),
    ((2, 3), "L"),
    ((0, 1), "L"),  # 2 L
    ((0, 1), "R"),  # 2 R
    ((1, 1), "D"),  # 6 D
    ((1, 3), "D"),  # 8 D
    ((2, 0), "L"),  # 9 L
    ((2, 0), "D"),  # 9 D
    ((1, 2), "U"),  # 7 U
    ((3, 2), "U"),  # 15 U
    ((3, 2), "L"),  # 15 L
    ((3, 0), "D"),  # 5 D
]
Z_T = [2, 1, 1, 1, 0.1, 1, 0.1, 0.1, 2, 0.1]  # Example sensor readings
P_FREE = 0.1
P_OCCUPIED = 0.8
current_state = 0


def send_to_esp32(command):
    global websocket_client
    if websocket_client is not None:
        message = json.dumps({"event": "command", "command": command})
        asyncio.run(websocket_client.send_text(message))


def handle_keyboard():
    def on_press(key):
        try:
            if hasattr(key, "char") and key.char in COMMANDS:
                send_to_esp32(COMMANDS[key.char])
        except AttributeError:
            pass

    def on_release(key):
        try:
            if hasattr(key, "char") and key.char in COMMANDS:
                send_to_esp32(COMMANDS["c"])
        except AttributeError:
            pass

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


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


@app.get("/")
async def index():
    return "WebSocket server is running!"


@app.get("/calculate")
async def calculate():
    global calculate_
    calculate_ = True

    return {"message": "Calculating grid"}


# use the above using the following curl command
# curl -X GET "http://localhost:8005/calculate"


@app.get("/reset_state")
async def reset_state():
    global current_state, calculate_
    current_state = 0
    calculate_ = False
    return {"message": "Resetting current state"}


@app.get("/reset_ws")
async def reset_ws():
    global websocket_client
    send_to_esp32(COMMANDS["c"])
    websocket_client = None
    return {"message": "Resetting WebSocket client"}


@app.websocket("/ws/move")
async def websocket_endpoint(websocket: WebSocket):
    global websocket_client, calculate_, current_state
    websocket_client = websocket
    await websocket.accept()

    grid = OccupancyGrid(GRID_SIZE, STATE_DIRECTIONS, P_FREE, P_OCCUPIED)
    previous_li = [0] * GRID_SIZE**2
    li = [0] * GRID_SIZE**2
    current_state = 0

    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            event = data.get("event")

            if event == "distance":
                distance_value = data.get("value")
                print(f"Received distance: {distance_value} mm")
                # await websocket_client.send_text(
                #     json.dumps({"event": "distance_frontend", "value": distance_value})
                # )
                if calculate_:
                    calculate_ = False
                    state = STATE_DIRECTIONS[current_state][0]
                    direction = STATE_DIRECTIONS[current_state][1]
                    range_ = int(distance_value / 300) if distance_value >= 1 else 0
                    if range_ > 5:
                        range_ = 5
                    if distance_value > 850:
                        range_ = 3

                    grid.update_individual_grid_column(
                        current_state, state, direction, range_, current_state == 0
                    )
                    grid.display_grid()
                    current_state += 1

                if current_state == len(STATE_DIRECTIONS):
                    grid.calculate_pm()
                    print(f"Probability Map: {grid.pm}")
                    save_probability_map(grid.pm, grid.grid_size)
                    # await websocket_client.send_text(
                    #     json.dumps(
                    #         {
                    #             "event": "calculate_pm",
                    #             "value": grid.pm.tolist(),
                    #         }
                    #     )
                    # )
                    current_state = 0

            if event == "update_matrix":
                distance = data.get("distance")
                state = STATE_DIRECTIONS[current_state][0]
                direction = STATE_DIRECTIONS[current_state][1]
                range_ = int(distance / 300) if distance >= 1 else 0

                grid.update_individual_grid_column(
                    current_state, state, direction, range_
                )
                grid.display_grid()
                await websocket_client.send_text(
                    json.dumps(
                        {
                            "event": "update_matrix_frontend",
                            "value": grid.grid.tolist(),
                        }
                    )
                )
                current_state += 1

            elif event == "collision":
                pass
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()


if __name__ == "__main__":
    threading.Thread(target=handle_keyboard, daemon=True).start()

    import uvicorn
    import asyncio

    async def main():
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8005,
        )

    import nest_asyncio

    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
