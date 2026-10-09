from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Optional

import chess

from board_manager import BoardManager, BoardManagerError
from chess_engine import StockfishAnalyzer


class ChessAssistantApp(tk.Tk):
    def __init__(
        self,
        board_manager: Optional[BoardManager] = None,
        engine_path: Optional[str] = None,
        analysis_time: float = 1.5,
        depth: int = 14,
    ) -> None:
        super().__init__()
        self.title("AI Chess Assistant")
        self.geometry("930x760")
        self.board_manager = board_manager or BoardManager()
        self.engine = StockfishAnalyzer(engine_path=engine_path, analysis_time=analysis_time, depth=depth)
        self.selected_square: Optional[int] = None
        self.legal_dests: set[int] = set()
        self.board_buttons: dict[int, tk.Button] = {}

        self.status_var = tk.StringVar(value="White to move")
        self.analysis_var = tk.StringVar(value="No evaluation available")

        self._build_layout()
        self._draw_board()

    def _build_layout(self) -> None:
        self.toolbar = tk.Frame(self)
        self.toolbar.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Button(self.toolbar, text="New Game", command=self.new_game).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="Load FEN", command=self.load_fen_dialog).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="Undo", command=self.undo_move).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="Redo", command=self.redo_move).pack(side=tk.LEFT, padx=5)
        tk.Button(self.toolbar, text="Analyze Best Move", command=self.analyze_best_move).pack(side=tk.LEFT, padx=5)

        self.board_frame = tk.Frame(self)
        self.board_frame.pack(padx=10, pady=10)

        self.status_label = tk.Label(self, textvariable=self.status_var, font=("Arial", 12, "bold"))
        self.status_label.pack(anchor="w", padx=10)

        self.analysis_label = tk.Label(self, textvariable=self.analysis_var, font=("Arial", 11), justify=tk.LEFT)
        self.analysis_label.pack(anchor="w", padx=10, pady=(5, 0))

    def _draw_board(self) -> None:
        for child in self.board_frame.winfo_children():
            child.destroy()
        self.board_buttons.clear()

        for rank in range(8):
            for file in range(8):
                square = chess.square(file, 7 - rank)
                button = tk.Button(
                    self.board_frame,
                    width=5,
                    height=2,
                    font=("Arial", 26),
                    command=lambda sq=square: self.handle_square_click(sq),
                    borderwidth=1,
                    relief="solid",
                )
                button.grid(row=rank, column=file, sticky="nsew")
                self.board_buttons[square] = button

        for file in range(8):
            self.board_frame.grid_columnconfigure(file, weight=1)
        for rank in range(8):
            self.board_frame.grid_rowconfigure(rank, weight=1)

        self.refresh_board()

    def refresh_board(self) -> None:
        for square, button in self.board_buttons.items():
            piece = self.board_manager.board.piece_at(square)
            symbol = ""
            if piece is not None:
                symbols = {
                    chess.Piece(chess.PAWN, chess.WHITE): "♙",
                    chess.Piece(chess.KNIGHT, chess.WHITE): "♘",
                    chess.Piece(chess.BISHOP, chess.WHITE): "♗",
                    chess.Piece(chess.ROOK, chess.WHITE): "♖",
                    chess.Piece(chess.QUEEN, chess.WHITE): "♕",
                    chess.Piece(chess.KING, chess.WHITE): "♔",
                    chess.Piece(chess.PAWN, chess.BLACK): "♟",
                    chess.Piece(chess.KNIGHT, chess.BLACK): "♞",
                    chess.Piece(chess.BISHOP, chess.BLACK): "♝",
                    chess.Piece(chess.ROOK, chess.BLACK): "♜",
                    chess.Piece(chess.QUEEN, chess.BLACK): "♛",
                    chess.Piece(chess.KING, chess.BLACK): "♚",
                }
                symbol = symbols.get(piece, "")

            is_light_square = (chess.square_file(square) + chess.square_rank(square)) % 2 == 0
            base_color = "#f0d9b5" if is_light_square else "#b58863"
            if square == self.selected_square:
                base_color = "#ffdd57"
            elif square in self.legal_dests:
                base_color = "#7bd389"

            button.config(text=symbol, bg=base_color, fg="black")

        self.status_var.set(self.board_manager.evaluate_game_state())

    def handle_square_click(self, square: int) -> None:
        if self.board_manager.board.is_game_over():
            messagebox.showinfo("Game Over", "The game is already over.")
            return

        if self.selected_square is not None:
            legal_moves = self.board_manager.legal_moves_for_square(self.selected_square)
            destinations = {move.to_square for move in legal_moves}
            if square in destinations:
                move = next(move for move in legal_moves if move.to_square == square)
                try:
                    self.board_manager.make_move(move)
                except BoardManagerError as exc:
                    messagebox.showerror("Invalid Move", str(exc))
                self.selected_square = None
                self.legal_dests.clear()
                self.refresh_board()
                return

        if self.board_manager.board.piece_at(square) is not None:
            piece = self.board_manager.board.piece_at(square)
            if piece is None or piece.color != self.board_manager.board.turn:
                return
            self.selected_square = square
            self.legal_dests = {move.to_square for move in self.board_manager.legal_moves_for_square(square)}
            self.refresh_board()
        else:
            self.selected_square = None
            self.legal_dests.clear()
            self.refresh_board()

    def new_game(self) -> None:
        self.board_manager = BoardManager()
        self.selected_square = None
        self.legal_dests.clear()
        self.refresh_board()

    def load_fen_dialog(self) -> None:
        fen = simpledialog.askstring("Load FEN", "Enter a FEN string:")
        if not fen:
            return
        try:
            self.board_manager.load_fen(fen)
            self.selected_square = None
            self.legal_dests.clear()
            self.refresh_board()
        except BoardManagerError as exc:
            messagebox.showerror("Invalid FEN", str(exc))

    def undo_move(self) -> None:
        try:
            self.board_manager.undo()
            self.selected_square = None
            self.legal_dests.clear()
            self.refresh_board()
        except BoardManagerError as exc:
            messagebox.showerror("Undo", str(exc))

    def redo_move(self) -> None:
        try:
            self.board_manager.redo()
            self.selected_square = None
            self.legal_dests.clear()
            self.refresh_board()
        except BoardManagerError as exc:
            messagebox.showerror("Redo", str(exc))

    def analyze_best_move(self) -> None:
        if not self.engine.is_available:
            messagebox.showwarning(
                "Stockfish missing",
                "Install Stockfish or set STOCKFISH_EXECUTABLE before analyzing the position.",
            )
            return

        recommendation = self.engine.recommend_move(self.board_manager.board)
        if recommendation is None:
            self.analysis_var.set("No move available: the position is over.")
            return

        self.analysis_var.set(
            f"Best move: {recommendation['san']} ({recommendation['uci']}) | "
            f"Evaluation: {recommendation['evaluation']} | PV: {' '.join(recommendation['principal_variation'])}"
        )
