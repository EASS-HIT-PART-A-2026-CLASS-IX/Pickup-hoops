from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class GameStatus(str, Enum):
    OPEN = "open"
    FULL = "full"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class User(SQLModel, table=True):
    """Represents an authenticated user."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    role: str = Field(default="user")


class GamePlayer(SQLModel, table=True):
    """Link table for many-to-many relationship between Game and Player."""
    game_id: int = Field(foreign_key="game.id", primary_key=True)
    player_id: int = Field(foreign_key="player.id", primary_key=True)


class Court(SQLModel, table=True):
    """Represents a basketball court location."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    city: str
    num_courts: int
    has_lighting: bool = False

    # Relationships
    games: List["Game"] = Relationship(back_populates="court")


class CourtCreate(SQLModel):
    name: str
    address: str
    city: str
    num_courts: int
    has_lighting: bool = False


class CourtUpdate(SQLModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    num_courts: Optional[int] = None
    has_lighting: Optional[bool] = None


class Player(SQLModel, table=True):
    """Represents a player in the pick-up hoops system."""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    city: str
    skill_level: SkillLevel

    # Many-to-many relationship with Game through GamePlayer
    games: List["Game"] = Relationship(
        back_populates="players",
        link_model=GamePlayer       
    )


class PlayerCreate(SQLModel):
    name: str
    city: str
    skill_level: SkillLevel


class PlayerUpdate(SQLModel):
    name: Optional[str] = None
    city: Optional[str] = None
    skill_level: Optional[SkillLevel] = None


class PlayerRead(SQLModel):
    id: int
    name: str
    city: str
    skill_level: SkillLevel


class Game(SQLModel, table=True):
    """Represents a pick-up basketball game."""
    id: Optional[int] = Field(default=None, primary_key=True)
    scheduled_time: datetime
    court_id: int = Field(foreign_key="court.id")
    skill_level: SkillLevel
    max_players: int
    status: GameStatus = GameStatus.OPEN

    # Relationships
    court: Court = Relationship(back_populates="games")
    players: List[Player] = Relationship(
        back_populates="games",
        link_model=GamePlayer
    )


class GameCreate(SQLModel):
    scheduled_time: datetime
    court_id: int
    skill_level: SkillLevel
    max_players: int
    status: GameStatus = GameStatus.OPEN


class GameUpdate(SQLModel):
    scheduled_time: Optional[datetime] = None
    court_id: Optional[int] = None
    skill_level: Optional[SkillLevel] = None
    max_players: Optional[int] = None
    status: Optional[GameStatus] = None


class GameRead(SQLModel):
    id: int
    scheduled_time: datetime
    court_id: int
    skill_level: SkillLevel
    max_players: int
    status: GameStatus
    players: List[PlayerRead] = []


