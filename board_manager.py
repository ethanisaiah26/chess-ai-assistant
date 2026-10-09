from __future__ import annotations

import os
import shutil
from typing import Any

import chess
import chess.engine


def find_stockfish_executable() -> str | None:
    """Search for a usable Stockfish binary in common locations."""
    env_path = os.getenv("STOCKFISH_EXECUTABLE")
    if env_path and os.path.exists(env_path):
        return env_path

    candidates = [
        "stockfish",
        "stockfish-ubuntu-x86-64",
        "stockfish-ubuntu-x86_64",
        "stockfish-ubuntu",
        "/usr/games/stockfish",
        "/usr/local/bin/stockfish",
        "/opt/stockfish/stockfish",
    ]

    for candidate in candidates:
        resolved = shutil.which(candidate) if not os.path.isabs(candidate) else candidate
        if resolved and os.path.exists(resolved):
            return resolved

    return None


class EngineStartupError(RuntimeError):
    """Raised when Stockfish cannot be started."""


class StockfishAnalyzer:
    def __init__(self, engine_path: str | None = None, depth: int = 14, analysis_time: float = 1.5) -> None:
        self.engine_path = engine_path or find_stockfish_executable()
        self.depth = depth
        self.analysis_time = analysis_time

    @property
    def is_available(self) -> bool:
        return bool(self.engine_path)

    def _start_engine(self):
        if not self.engine_path:
            raise EngineStartupError(
                "Stockfish executable was not found. Install Stockfish or set STOCKFISH_EXECUTABLE."
            )
        try:
            return chess.engine.SimpleEngine.popen_uci(self.engine_path)
        except OSError as exc:
            raise EngineStartupError(f"Failed to start Stockfish at {self.engine_path}: {exc}") from exc

    def analyze_position(self, board: chess.Board) -> dict[str, Any]:
        engine = self._start_engine()
        try:
            limit = chess.engine.Limit(depth=self.depth, time=self.analysis_time)
            info = engine.analyse(board, limit)
            score = info.get("score")
            pv = info.get("pv", [])

            if not pv:
                return {
                    "san": "N/A",
                    "uci": "",
                    "evaluation": "No legal move available",
                    "principal_variation": [],
                }

            temp_board = board.copy()
            principal_variation = []
            for move in pv[:8]:
                principal_variation.append(temp_board.san(move))
                temp_board.push(move)

            if score is None:
                return {
                    "san": principal_variation[0],
                    "uci": pv[0].uci(),
                    "evaluation": "No evaluation available",
                    "principal_variation": principal_variation,
                }

            score_for_side = score.pov(board.turn)
            evaluation = self._format_score(score_for_side)
            best_move = pv[0]
            san = board.san(best_move)

            return {
                "san": san,
                "uci": best_move.uci(),
                "evaluation": evaluation,
                "principal_variation": principal_variation,
            }
        finally:
            engine.quit()

    def recommend_move(self, board: chess.Board) -> dict[str, Any] | None:
        if board.is_game_over():
            return None
        return self.analyze_position(board)

    @staticmethod
    def _format_score(score: chess.engine.Score) -> str:
        if score.is_mate():
            mate_moves = score.mate()
            side = "White" if mate_moves > 0 else "Black"
            return f"Mate in {abs(mate_moves)} for {side}"

        cp_value = score.score() / 100.0
        return f"{cp_value:+.2f} pawns"
