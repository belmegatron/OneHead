from onehead.game import Game

class GameStore:
    def __init__(self) -> None:
        self.current_game: Game | None = None
        self.previous_game: Game | None = None