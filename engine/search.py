"""Search for the chess engine: negamax and alpha-beta."""
from engine.evaluate import evaluate
from engine.movegen import legal_moves, is_attacked

# Larger than any material score
MATE = 100000
INF = float("inf")


def no_moves_score(board, depth):
    """Score a position with no legal moves: checkmate or stalemate."""
    king_sq = board.squares.index("K" if board.turn == "w" else "k")
    if is_attacked(board, king_sq, by_white=(board.turn == "b")):
        # Checkmated. Adding the remaining depth makes a faster mate score better
        return -MATE - depth
    return 0  # stalemate is a draw


def negamax(board, depth):
    """Plain negamax. Slow, kept to verify that alpha-beta gives the same score."""
    if depth == 0:
        return evaluate(board)
    moves = legal_moves(board)
    if not moves:
        return no_moves_score(board, depth)
    best = -INF
    for move in moves:
        # My score is the negative of my opponent's score after my move
        best = max(best, -negamax(board.make_move(move), depth - 1))
    return best


def alphabeta(board, depth, alpha, beta):
    """Negamax with alpha-beta pruning. alpha = best I can guarantee, beta = best the opponent allows."""
    if depth == 0:
        return evaluate(board)
    moves = legal_moves(board)
    if not moves:
        return no_moves_score(board, depth)
    for move in moves:
        # The window flips sign and swaps for the opponent
        score = -alphabeta(board.make_move(move), depth - 1, -beta, -alpha)
        if score >= beta:
            return beta  # opponent won't allow this line, cut off
        if score > alpha:
            alpha = score  # new best for me
    return alpha


def best_move(board, depth):
    """Return (best move, score) for the side to move."""
    alpha, beta = -INF, INF
    best_mv = None
    for move in legal_moves(board):
        score = -alphabeta(board.make_move(move), depth - 1, -beta, -alpha)
        # The first move always becomes the fallback, even if its score is poor
        if best_mv is None or score > alpha:
            alpha = max(alpha, score)
            best_mv = move
    return best_mv, alpha