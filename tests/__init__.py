from __future__ import annotations

import pytest
import chess

from board_manager import BoardManager, BoardManagerError
from chess_engine import find_stockfish_executable


def test_starting_position_is_valid() -> None:
    board = BoardManager()
    assert board.board.fen() == chess.STARTING_FEN
    assert board.board.turn == chess.WHITE


def test_legal_move_is_accepted() -> None:
    board = BoardManager()
    move = board.make_move("e4")
    assert move == chess.Move.from_uci("e2e4")
    assert board.board.fen().startswith("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR")


def test_illegal_move_is_rejected() -> None:
    board = BoardManager()
    with pytest.raises(BoardManagerError):
        board.make_move("e5")


def test_fen_loading_updates_position() -> None:
    board = BoardManager()
    board.load_fen("8/8/8/8/8/8/8/4K2R w - - 0 1")
    assert board.board.king(chess.WHITE) == chess.square(4, 0)
    assert board.turn_name == "White"


def test_import_export_pgn_round_trip() -> None:
    board = BoardManager()
    board.make_move("e4")
    board.make_move("e5")
    pgn = board.export_pgn("Test Game")
    new_board = BoardManager()
    new_board.import_pgn(pgn)
    assert len(new_board._move_history) == 2
    assert new_board.board.fen() == board.board.fen()


@pytest.mark.skipif(find_stockfish_executable() is None, reason="Stockfish not installed")
def test_engine_recommendation_returns_move() -> None:
    from chess_engine import StockfishAnalyzer

    analyzer = StockfishAnalyzer(depth=10, analysis_time=0.2)
    board = BoardManager()
    recommendation = analyzer.recommend_move(board.board)
    assert recommendation is not None
    assert "san" in recommendation
    assert "uci" in recommendation
