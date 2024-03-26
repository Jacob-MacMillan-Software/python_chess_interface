#!/usr/bin/env python3

"""
This library is a simple UCI (Universal Chess Interface) client for Python 3. It
is designed to be easy to use with any python chess engine that wishes to support UCI.

This should handle all commands mostly on its own, but it is up to the user to
handle the engine's responses.

This library is free software: you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option)
any later version.

This library is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License along
with this library.  If not, see <http://www.gnu.org/licenses/>.

Author: 2024, Jacob MacMillan Software Inc. (Jacob MacMillan)
"""

import sys
import time
from queue import Queue
from typing import Callable
import threading
import chess

# The UCI class is the main class that you will use to interact with the engine.
# It must take the move search function as an argument, and that function is expected to be able
# to handle the "go" and "stop" commands, as well as adhere to any time limits that are set.
# The move search function must take at least the current position string,
# the time limit in milliseconds as arguments, and for max depth,
# and a Queue to recieve messages so it can know if  the stop command was sent,
# and also to send the current best move to the UCI class.
# Any return value is ignored, and the best move is sent to the UCI class via the Queue.
# Everything else is handled by the UCI class.

class UCI:
    def __init__(
            self,
            move_search: Callable[[str, int, int, Queue, Queue], None],
            author: str = "(UCI Implementation) Jacob MacMillan Software Inc.",
            engine_name: str = "UCI Chess Engine"
            ):
        self.move_search = move_search
        self.best_move = None # The best move found by the engine so far, in UCI format
        self.position = "startpos" # Starting position
        self.time_limit = 0 # Time limit in milliseconds
        self.send_queue = Queue() # Queue used to send information to the engine
        self.recv_queue = Queue() # Queue used to recieve information from the engine
        self.max_depth = 0
        self.author = author
        self.engine_name = engine_name
        self.position = "startpos"
        self.move_thread = None

    def read(self) -> str:
        """
        Reads a single input line from stdin, processes it, and returns.
        Force closes the program if we recieve "quit"

        Ignore invalid/empty commands

        :return: None
        """

        command = input().strip()

        self.process_command(command)

        return command

    def process_command(self, command: str):
        """
        Processes a single command from the engine.

        A good description of the UCI protocol can be found here:
        https://www.wbec-ridderkerk.nl/html/UCIProtocol.html

        :param command: The command to process
        :return: None
        """

        if command == "uci":
            self.send("id name " + self.engine_name)
            self.send("id author " + self.author)
            self.send("uciok")
        elif command == "isready":
            self.send("readyok")
        elif command.startswith("position"):
            # Constrcut the position fen based on the starting position fen plus any given moves
            self.position = "startpos"
            args = command.split(" ")

            chess_board = chess.Board()

            if args[1] != "startpos":
                if args[1] == "fen":
                    self.position = " ".join(args[2:8])

            chess_board = chess.Board(self.position)

            if len(args) > 8 and args[8] == "moves":
                for i in range(9, len(args)):
                    chess_board.push(chess.Move.from_uci(args[i]))

            self.position = chess_board.fen()
        elif command.startswith("go"):
            # Clear queues and kill the thread if it is running
            if self.move_thread is not None:
                self.send_queue.put("stop")
                self.move_thread.join()
                self.move_thread = None
            while not self.send_queue.empty():
                self.send_queue.get()
            while not self.recv_queue.empty():
                self.recv_queue.get()

            # Parse the arguments
            args = command.split(" ")
            time_limit = 0
            max_depth = 0

            for i in range(1, len(args)):
                if args[i] == "movetime":
                    time_limit = int(args[i + 1]) 
                elif args[i] == "depth":
                    max_depth = int(args[i + 1])
                elif args[i] == "infinite":
                    time_limit = 999999999
                # TODO: Need to handle time control information
                # winc, binc, wtime, btime, movestogo
                # TODO: need to handle ponder, mate, and searchmoves

            # Start the move search on a new thread
            self.move_thread = threading.Thread(
                target=self.move_search,
                args=(self.position, time_limit, max_depth, self.recv_queue, self.send_queue)
            )

            self.move_thread.start()

        elif command.startswith("stop"):
            self.send_queue.put("stop")
            # Wait until the recv_queue has a message in it, and then kill the thread
            while self.recv_queue.empty():
                time.sleep(0.1)
            self.best_move = self.recv_queue.get()

            # Make sure the thread is dead
            self.move_thread.join()

            # Output the best move
            # Use just bestmove if the value is a str, or bestmove and ponder if it is a tuple or list
            if isinstance(self.best_move, str):
                self.send("bestmove " + self.best_move)
            elif isinstance(self.best_move, (list, tuple)):
                self.send("bestmove " + self.best_move[0] + " ponder " + self.best_move[1])
        elif command.startswith("ucinewgame"):
            self.position = "startpos"
        elif command.startswith("setoption"):
            # This is very engine specific, so we will just ignore it for now
            pass
        elif command.startswith("quit"):
            sys.exit(0)
        else:
            pass

    def send(self, text: str):
        """
        Prints output to stdout

        :param command: The command to send
        :return: None
        """

        print(text, flush=True)

    def check_best_move(self):
        """
        Checks if the search has completed, and if so we will print out the best move and
        return True, otherwise return False.
        """

        if self.move_thread is not None:
            if self.move_thread.is_alive():
                return False
            self.move_thread.join()
            self.move_thread = None
        if not self.recv_queue.empty():
            self.best_move = self.recv_queue.get()
            if isinstance(self.best_move, str):
                self.send("bestmove " + self.best_move)
            elif isinstance(self.best_move, (list, tuple)):
                self.send("bestmove " + self.best_move[0] + " ponder " + self.best_move[1])
            return True
        return False
