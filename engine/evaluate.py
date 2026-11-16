"""Static evaluation: material only, scored from the side to move's point of view."""

# Piece values in centipawns (100 = one pawn). The king is 0 because it can never be captured.
PIECE_VALUES = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 0}


def evaluate(board):
    """Return the material balance in centipawns.

    Positive means the side to move is better, negative means it is worse.
    This is the convention negamax search relies on.
    """
    white_score = 0
    for piece in board.squares:
        if piece == ".":
            continue
        value = PIECE_VALUES[piece.lower()]
        # Uppercase = White (adds), lowercase = Black (subtracts)
        white_score += value if piece.isupper() else -value
    # Flip once so the score is from the side to move's view
    return white_score if board.turn == "w" else -white_score