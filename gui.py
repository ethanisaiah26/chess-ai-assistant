from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional, Union

import chess
import chess.pgn


class BoardManagerError(ValueError):
    """Raised when a board action cannot be completed."""


@dataclass
class MoveExplanation:
    text: str
    tactical_hint: Optional[str] = None


class BoardManager:
    def __init__(self, fen: Optional[str] = None) -> None:
        self.board = chess.Board(fen or chess.STARTING_FEN)
        self._move_history: list[chess.Move] = []
        self._redo_stack: list[chess.Move] = []

    @property
    def turn_name(self) -> str:
        return "White" if self.board.turn else "Black"

    def load_fen(self, fen: str) -> None:
        try:
            self.board = chess.Board(fen)
        except ValueError as exc:
            raise BoardManagerError(f"Invalid FEN: {fen}") from exc
        self._move_history.clear()
        self._redo_stack.clear()

    def make_move(self, move: Union[str, chess.Move]) -> chess.Move:
        if isinstance(move, str):
            move_text = move.strip()
            try:
                if len(move_text) in {4, 5}:
                    candidate = chess.Move.from_uci(move_text)
                else:
                    candidate = self.board.parse_san(move_text)
            except ValueError as exc:
                raise BoardManagerError(f"Invalid move notation: {move_text}") from exc
        else:
            candidate = move

        if candidate not in self.board.legal_moves:
            raise BoardManagerError(f"Illegal move: {candidate.uci()}")

        self._redo_stack.clear()
        self._move_history.append(candidate)
        self.board.push(candidate)
        return candidate

    def undo(self) -> chess.Move:
        if not self._move_history:
            raise BoardManagerError("Nothing to undo.")
        last_move = self._move_history.pop()
        self._redo_stack.append(last_move)
        self.board.pop()
        return last_move

    def redo(self) -> chess.Move:
        if not self._redo_stack:
            raise BoardManagerError("Nothing to redo.")
        move = self._redo_stack.pop()
        self._move_history.append(move)
        self.board.push(move)
        return move

    def legal_moves_for_square(self, square: int) -> list[chess.Move]:
        return [move for move in self.board.legal_moves if move.from_square == square]

    def export_pgn(self, event_name: str = "Practice") -> str:
        game = chess.pgn.Game()
        game.headers["Event"] = event_name
        game.headers["Site"] = "Local Chess Assistant"
        game.headers["Date"] = "2026.10.09"
        game.headers["Round"] = "1"

        node = game
        for move in self._move_history:
            node = node.add_variation(move)
        return str(game)

    def import_pgn(self, pgn_text: str) -> None:
        try:
            parsed = chess.pgn.read_game(io.StringIO(pgn_text))
        except Exception as exc:
            raise BoardManagerError(f"Unable to parse PGN: {exc}") from exc

        if parsed is None:
            raise BoardManagerError("No PGN content was found.")

        board = parsed.board()
        moves = list(parsed.mainline_moves())
        for move in moves:
            board.push(move)

        self.board = board
        self._move_history = moves
        self._redo_stack.clear()

    def explain_move(self, move: chess.Move) -> MoveExplanation:
        current_board = self.board.copy()
        if move not in current_board.legal_moves:
            raise BoardManagerError(f"Illegal move for explanation: {move.uci()}")

        piece = current_board.piece_at(move.from_square)
        if piece is None:
            raise BoardManagerError("The source square is empty.")

        next_board = current_board.copy()
        next_board.push(move)

        text_parts: list[str] = []
        piece_symbol = piece.symbol()
        text_parts.append(f"{piece_symbol} moves to {chess.square_name(move.to_square)}.")

        if current_board.is_capture(move):
            captured_piece = current_board.piece_at(move.to_square)
            captured_symbol = captured_piece.symbol() if captured_piece else "piece"
            text_parts.append(f"It captures the {captured_symbol}.")

        if next_board.is_check():
            text_parts.append("This gives check.")
        if next_board.is_checkmate():
            text_parts.append("This is checkmate.")
        elif next_board.is_stalemate():
            text_parts.append("This results in stalemate.")

        tactical_hint: Optional[str] = None
        if next_board.is_check():
            tactical_hint = "check"
        elif current_board.is_capture(move):
            tactical_hint = "capture"
        elif move.promotion is not None:
            tactical_hint = "promotion"

        return MoveExplanation(text=" ".join(text_parts), tactical_hint=tactical_hint)

    def evaluate_game_state(self) -> str:
        if self.board.is_checkmate():
            return f"Checkmate - {self.turn_name} to move"
        if self.board.is_stalemate():
            return "Stalemate"
        if self.board.is_insufficient_material():
            return "Insufficient material - draw"
        if self.board.is_seventy_five_moves():
            return "75-move rule - draw"
        if self.board.is_fivefold_repetition():
            return "Fivefold repetition - draw"
        if self.board.is_check():
            return f"{self.turn_name} is in check"
        return f"{self.turn_name} to move"
