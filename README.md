# Chess Interface

This package is intended to provide drop-in support for UCI for chess engines.

This probably isn't possible, in reality, but the goal of this project is to be able to simply add this to any python chess engine without having to change any of the actual engine code.
However, since UCI requires time limit and a stop command, the engine will likely need to be adjusted in some way to support those. Engines may work with this package without supporting timers or 
the stop command, however this could cause undefined behaviour with many chess clients. For example, a chess client may set depth to 99 (unlimited) with no time limit and intend to send a stop
command after a given length of time.
