#!/usr/bin/env python3

"""
Example chess engine just to test the UCI library.

It just returns a random legal move, after waiting for the entire time limit to pass.
"""

import random
import time
from queue import Queue
from typing import Callable
import chess

import main as uci

def move_search(
        position: str,
        time_limit: int,
        max_depth: int,
        send_queue: Queue,
        recv_queue: Queue
        ):
    """
    Waits for the stop command or the time to expire, and then sends a random legal move
    """
    # Parse the position
    board = chess.Board()
    if position != "startpos":
        board.set_fen(position)

    # Generate all legal moves
    legal_moves = list(board.legal_moves)

    # Wait for the time limit to pass or to receive a stop command from the recv_queue
    start_time = time.time()
    while time.time() - start_time < time_limit:
        if not recv_queue.empty():
            command = recv_queue.get()
            if command == "stop":
                break

    # Pick a random move
    move = random.choice(legal_moves)
    send_queue.put(str(move))

if __name__ == "__main__":
    print("Chess Interface Test Engine by Jacob MacMillan Software Inc.")
    interface = uci.UCI(move_search)
    while True:
        command = interface.read()

        # Save the command to the log file for debugging
        with open("log.txt", "a") as log:
            log.write(command + "\n")
        interface.check_best_move()
