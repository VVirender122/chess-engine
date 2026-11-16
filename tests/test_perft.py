"""Perft tests: count legal-move paths and compare them with known values and python-chess."""
import sys
import time
import chess  # referee only, the engine itself never imports it
from engine.board import Board
from engine.movegen import legal_moves

# (name, fen, depth, expected leaf count)
TESTS = [
    ("start", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 3, 8902),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 2, 2039),
    ("position 3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 3, 2812),
    ("position 4", "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", 2, 264),
]

# Slower checks, run with --deep (can take a minute or more each in pure Python)
DEEP_TESTS = [
    ("start", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", 5, 197281),
    ("kiwipete", "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 3, 97862),
    ("position 3", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 4, 43238),
]


def perft(board, depth):
    """Count leaf positions reachable in exactly `depth` legal moves (your engine)."""
    if depth == 0:
        return 1
    moves = legal_moves(board)
    if depth == 1:
        return len(moves)  # shortcut: no need to play the last move
    return sum(perft(board.make_move(m), depth - 1) for m in moves)


def perft_ref(ref, depth):
    """Same count using python-chess. Gives the expected value for any new position."""
    if depth == 0:
        return 1
    if depth == 1:
        return ref.legal_moves.count()
    total = 0
    for move in list(ref.legal_moves):
        ref.push(move)
        total += perft_ref(ref, depth - 1)
        ref.pop()
    return total


def run_tests(tests):
    """Run each test, print the result, and return True if all passed."""
    all_ok = True
    for name, fen, depth, expected in tests:
        start = time.time()
        result = perft(Board(fen), depth)
        status = "OK" if result == expected else "MISMATCH"
        print(f"{name:<11} depth {depth}: got {result}, expected {expected} -> {status} ({time.time() - start:.1f}s)")
        if result != expected:
            all_ok = False
            print(f"  FEN: {fen}")
            print(f"  Debug with: python -m tests.test_perft divide \"{fen}\" {depth}")
    return all_ok


def divide(fen, depth):
    """Print per-move counts from both engines and show where they disagree."""
    board = Board(fen)
    ref = chess.Board(fen)

    mine = {m.uci(): perft(board.make_move(m), depth - 1) for m in legal_moves(board)}

    theirs = {}
    for move in list(ref.legal_moves):
        ref.push(move)
        theirs[move.uci()] = perft_ref(ref, depth - 1)
        ref.pop()

    print(f"Yours: {sum(mine.values())}   Reference: {sum(theirs.values())}")
    problems = 0
    for uci in sorted(set(mine) | set(theirs)):
        if uci not in mine:
            print(f"  {uci}: MISSING from your generator (reference has {theirs[uci]})")
            problems += 1
        elif uci not in theirs:
            print(f"  {uci}: ILLEGAL move in your generator (you have {mine[uci]})")
            problems += 1
        elif mine[uci] != theirs[uci]:
            print(f"  {uci}: yours {mine[uci]}, reference {theirs[uci]}")
            problems += 1
    if problems == 0:
        print("No differences at this depth.")
    else:
        print("Pick one differing move, play it, and run divide again from the new FEN at depth - 1.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "divide":
        # python -m tests.test_perft divide "<fen>" <depth>
        divide(args[1], int(args[2]))
    else:
        ok = run_tests(DEEP_TESTS if "--deep" in args else TESTS)
        print("All tests passed." if ok else "Some tests FAILED.")
        sys.exit(0 if ok else 1)