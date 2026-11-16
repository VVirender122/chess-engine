"""Move generation for the chess engine (kings and knights so far)."""
from engine.board import Move

# Each offset is (rank change, file change)
king_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
knight_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]

# sliding directions for bishops, rooks and queens
bishop_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
rook_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
queen_dirs = bishop_dirs + rook_dirs

def jump_moves(board, sq, offsets):
    """Generate pseudo-legal moves for a piece that jumps (knight, king)."""
    moves = []
    rank, file = divmod(sq, 8)
    mover_is_white = board.squares[sq].isupper()
    for dr, df in offsets:
        r, f = rank + dr, file + df
        # Checking rank and file separately stops wrap-around at the board edge
        if 0 <= r < 8 and 0 <= f < 8:
            to_sq = r * 8 + f
            target = board.squares[to_sq]
            # Allowed if the square is empty or holds an enemy piece
            if target == "." or target.isupper() != mover_is_white:
                moves.append(Move(sq, to_sq))
    return moves

def slide_moves(board, sq, directions):
    """Generate pseudo-legal moves for a sliding piece (bishop, rook, queen)."""
    moves = []
    rank, file = divmod(sq, 8)
    mover_is_white = board.squares[sq].isupper()
    for dr, df in directions:
        r, f = rank + dr, file + df
        while 0 <= r < 8 and 0 <= f < 8:
            to_sq = r * 8 + f
            target = board.squares[to_sq]
            if target == ".":
                moves.append(Move(sq, to_sq))
            else:
                # Stop sliding if we hit a piece; add a capture if it's an enemy
                if target.isupper() != mover_is_white:
                    moves.append(Move(sq, to_sq))
                break
            r += dr
            f += df
    return moves

def pawn_moves(board, sq):
    """Generate pseudo-legal moves for a pawn."""
    moves = []
    rank, file = divmod(sq, 8)
    mover_is_white = board.squares[sq].isupper()
    direction = 1 if mover_is_white else -1
    start_rank = 1 if mover_is_white else 6
    promotion_rank = 7 if mover_is_white else 0

    # One square forward
    one_forward_rank = rank + direction
    if 0 <= one_forward_rank < 8:
        one_forward_sq = one_forward_rank * 8 + file
        if board.squares[one_forward_sq] == ".":
            # Promotion check
            if one_forward_rank == promotion_rank:
                for promo_piece in ["q", "r", "b", "n"]:
                    moves.append(Move(sq, one_forward_sq, promo=promo_piece))
            else:
                moves.append(Move(sq, one_forward_sq))

            # Two squares forward from starting position
            if rank == start_rank:
                two_forward_rank = rank + 2 * direction
                two_forward_sq = two_forward_rank * 8 + file
                if board.squares[two_forward_sq] == ".":
                    moves.append(Move(sq, two_forward_sq))

    # Captures (including en passant)
    for df in [-1, 1]:
        capture_file = file + df
        if 0 <= capture_file < 8:
            capture_sq = one_forward_rank * 8 + capture_file
            target_piece = board.squares[capture_sq]
            if target_piece != "." and target_piece.isupper() != mover_is_white:
                # Promotion check for captures
                if one_forward_rank == promotion_rank:
                    for promo_piece in ["q", "r", "b", "n"]:
                        moves.append(Move(sq, capture_sq, promo=promo_piece))
                else:
                    moves.append(Move(sq, capture_sq))
            elif capture_sq == board.ep:  # En passant capture
                moves.append(Move(sq, capture_sq))

    return moves

def pseudo_legal_moves(board):
    """Generate all pseudo-legal moves for the side to move."""
    moves = []
    for sq, piece in enumerate(board.squares):
        if piece == ".":
            continue
        # Only generate moves for pieces belonging to the side to move
        if piece.isupper() == (board.turn == "w"):
            if piece.lower() == "n":
                moves.extend(jump_moves(board, sq, knight_offsets))
            elif piece.lower() == "k":
                moves.extend(jump_moves(board, sq, king_offsets))
            elif piece.lower() == "b":
                moves.extend(slide_moves(board, sq, bishop_dirs))
            elif piece.lower() == "r":
                moves.extend(slide_moves(board, sq, rook_dirs))
            elif piece.lower() == "q":
                moves.extend(slide_moves(board, sq, queen_dirs))
            elif piece.lower() == "p":
                moves.extend(pawn_moves(board, sq))
    # Castling moves are generated separately, since they involve multiple pieces and special rules
    moves.extend(castle_moves(board))
    return moves

def is_attacked(board, sq, by_white):
    """Return True if any piece of the given color attacks square sq."""
    rank, file = divmod(sq, 8)

    def enemy(letter):
        # Attacking piece letter in the attacker's case
        return letter.upper() if by_white else letter.lower()

    # Knights and kings: look at each offset square for the attacking piece
    for offsets, letter in ((knight_offsets, "n"), (king_offsets, "k")):
        for dr, df in offsets:
            r, f = rank + dr, file + df
            if 0 <= r < 8 and 0 <= f < 8 and board.squares[r * 8 + f] == enemy(letter):
                return True

    # Sliders: walk outward, the first piece hit decides the result
    for dirs, letter in ((bishop_dirs, "b"), (rook_dirs, "r")):
        for dr, df in dirs:
            r, f = rank + dr, file + df
            while 0 <= r < 8 and 0 <= f < 8:
                piece = board.squares[r * 8 + f]
                if piece != ".":
                    if piece in (enemy(letter), enemy("q")):
                        return True
                    break  # any other piece blocks the line
                r, f = r + dr, f + df

    # Pawns: a White pawn sits one rank below sq, a Black pawn one rank above
    pawn_rank = rank - 1 if by_white else rank + 1
    if 0 <= pawn_rank < 8:
        for df in (-1, 1):
            f = file + df
            if 0 <= f < 8 and board.squares[pawn_rank * 8 + f] == enemy("p"):
                return True
    return False

def legal_moves(board):
    """Generate all legal moves for the side to move."""
    moves = []
    for move in pseudo_legal_moves(board):
        new_board = board.make_move(move)
        king_sq = new_board.squares.index("K" if board.turn == "w" else "k")
        if not is_attacked(new_board, king_sq, by_white=(board.turn == "b")):
            moves.append(move)
    return moves

def castle_moves(board):
    """Generate legal castling moves for the side to move."""
    moves = []
    if board.turn == "w":
        king_sq = 4
        if "K" in board.castling and board.squares[4] == "K" and board.squares[7] == "R":
            if (board.squares[5] == board.squares[6] == "."
                    and not is_attacked(board, 4, by_white=False)
                    and not is_attacked(board, 5, by_white=False)
                    and not is_attacked(board, 6, by_white=False)):
                moves.append(Move(king_sq, 6))  # O-O
        if "Q" in board.castling and board.squares[0] == "R" and board.squares[4] == "K":
            if (board.squares[1] == board.squares[2] == board.squares[3] == "."
                    and not is_attacked(board, 4, by_white=False)
                    and not is_attacked(board, 3, by_white=False)
                    and not is_attacked(board, 2, by_white=False)):
                moves.append(Move(king_sq, 2))  # O-O-O
    else:
        king_sq = 60
        if "k" in board.castling and board.squares[60] == "k" and board.squares[63] == "r":
            if (board.squares[61] == board.squares[62] == "."
                    and not is_attacked(board, 60, by_white=True)
                    and not is_attacked(board, 61, by_white=True)
                    and not is_attacked(board, 62, by_white=True)):
                moves.append(Move(king_sq, 62))  # O-O
        if "q" in board.castling and board.squares[56] == "r" and board.squares[60] == "k":
            if (board.squares[57] == board.squares[58] == board.squares[59] == "."
                    and not is_attacked(board, 60, by_white=True)
                    and not is_attacked(board, 59, by_white=True)
                    and not is_attacked(board, 58, by_white=True)):
                moves.append(Move(king_sq, 58))  # O-O-O
    return moves