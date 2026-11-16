"""Board representation and Move type for the chess engine."""

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
FILES = "abcdefgh"
# Corner squares and the castling right lost when a piece leaves or lands on them
CORNER_RIGHTS = {0: "Q", 7: "K", 56: "q", 63: "k"}

def sq_name(sq):
    """Convert a square index (0-63) to algebraic name, e.g. 28 -> 'e4'."""
    return FILES[sq % 8] + str(sq // 8 + 1)


def sq_index(name):
    """Convert an algebraic name to a square index, e.g. 'e4' -> 28."""
    return (int(name[1]) - 1) * 8 + FILES.index(name[0])


class Move:
    """A move: from-square, to-square and an optional promotion piece."""
    __slots__ = ("frm", "to", "promo")

    def __init__(self, frm, to, promo=None):
        self.frm = frm
        self.to = to
        self.promo = promo  # lowercase letter: 'q', 'r', 'b', 'n' or None

    def uci(self):
        """Return the move in UCI text, e.g. 'e2e4' or 'e7e8q'."""
        return sq_name(self.frm) + sq_name(self.to) + (self.promo or "")

    def __repr__(self):
        return self.uci()

    def __eq__(self, other):
        return (self.frm, self.to, self.promo) == (other.frm, other.to, other.promo)

    def __hash__(self):
        return hash((self.frm, self.to, self.promo))


class Board:
    """Position state. Pieces are letters: uppercase = white, lowercase = black, '.' = empty."""

    def __init__(self, fen=START_FEN):
        self.set_fen(fen)

    def set_fen(self, fen):
        """Load a position from a FEN string."""
        parts = fen.split()
        self.squares = ["."] * 64
        # FEN lists rank 8 first, so we walk the ranks from 7 down to 0
        rank = 7
        file = 0
        for ch in parts[0]:
            if ch == "/":
                rank -= 1
                file = 0
            elif ch.isdigit():
                file += int(ch)  # a digit means that many empty squares
            else:
                self.squares[rank * 8 + file] = ch
                file += 1
        self.turn = parts[1]                                   # 'w' or 'b'
        self.castling = parts[2]                               # e.g. 'KQkq' or '-'
        self.ep = None if parts[3] == "-" else sq_index(parts[3])  # en passant target square
        self.halfmove = int(parts[4]) if len(parts) > 4 else 0  # moves since last capture/pawn move
        self.fullmove = int(parts[5]) if len(parts) > 5 else 1

    def fen(self):
        """Return the current position as a FEN string."""
        rows = []
        for rank in range(7, -1, -1):
            row = ""
            empty = 0
            for file in range(8):
                piece = self.squares[rank * 8 + file]
                if piece == ".":
                    empty += 1
                else:
                    if empty:
                        row += str(empty)
                        empty = 0
                    row += piece
            if empty:
                row += str(empty)
            rows.append(row)
        ep = "-" if self.ep is None else sq_name(self.ep)
        return f"{'/'.join(rows)} {self.turn} {self.castling} {ep} {self.halfmove} {self.fullmove}"

    def __str__(self):
        """Pretty-print the board with White at the bottom."""
        lines = []
        for rank in range(7, -1, -1):
            lines.append(str(rank + 1) + " " + " ".join(self.squares[rank * 8:rank * 8 + 8]))
        lines.append("  a b c d e f g h")
        return "\n".join(lines)

    def copy(self):
        """Return a copy of the board."""
        new_board = Board()
        new_board.squares = self.squares[:]
        new_board.turn = self.turn
        new_board.castling = self.castling
        new_board.ep = self.ep
        new_board.halfmove = self.halfmove
        new_board.fullmove = self.fullmove
        return new_board

    def make_move(self, move):
        """Return a new Board with the move applied. Does not check legality."""
        new = self.copy()
        piece = self.squares[move.frm]
        white = piece.isupper()
        kind = piece.lower()
        # Must be read before we overwrite the destination square
        is_capture = self.squares[move.to] != "."

        # En passant capture: a pawn moves diagonally onto the empty ep square,
        # and the captured pawn sits one rank behind the destination
        if kind == "p" and move.to == self.ep and move.frm % 8 != move.to % 8:
            captured_sq = move.to - 8 if white else move.to + 8
            new.squares[captured_sq] = "."
            is_capture = True

        # Move the piece, swapping in the promoted piece if there is one
        if move.promo:
            new.squares[move.to] = move.promo.upper() if white else move.promo.lower()
        else:
            new.squares[move.to] = piece
        new.squares[move.frm] = "."

        # Castling: the king moves two files, so the rook jumps to the other side of it
        if kind == "k" and abs(move.to - move.frm) == 2:
            if move.to > move.frm:                      # king side
                rook_from, rook_to = move.frm + 3, move.frm + 1
            else:                                       # queen side
                rook_from, rook_to = move.frm - 4, move.frm - 1
            new.squares[rook_to] = new.squares[rook_from]
            new.squares[rook_from] = "."

        # Castling rights: lost when the king moves...
        if kind == "k":
            lost = "KQ" if white else "kq"
            for right in lost:
                new.castling = new.castling.replace(right, "")
        # ...or when anything leaves or lands on a rook's corner (rook moved or captured)
        for corner, right in CORNER_RIGHTS.items():
            if move.frm == corner or move.to == corner:
                new.castling = new.castling.replace(right, "")
        if new.castling == "":
            new.castling = "-"                          # FEN uses '-' for no rights

        # En passant target: the skipped square after a two-square pawn push
        if kind == "p" and abs(move.to - move.frm) == 16:
            new.ep = (move.frm + move.to) // 2
        else:
            new.ep = None

        # Clocks: halfmove resets on a pawn move or capture, fullmove counts after Black
        new.halfmove = 0 if kind == "p" or is_capture else self.halfmove + 1
        if not white:
            new.fullmove += 1

        # Flip the turn
        new.turn = "b" if self.turn == "w" else "w"
        return new