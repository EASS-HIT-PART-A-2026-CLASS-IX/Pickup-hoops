from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from api.auth import create_access_token, require_admin, verify_password
from api.database import create_db_and_tables, get_session
from api.models import (
    Court,
    CourtCreate,
    CourtUpdate,
    Player,
    PlayerCreate,
    PlayerUpdate,
    Game,
    GameCreate,
    GameRead,
    GameUpdate,
    User,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (if needed)


app = FastAPI(title="Pick-Up Hoops API", lifespan=lifespan)


@app.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token({"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


# ============== COURT CRUD ROUTES ==============


@app.post("/courts/", response_model=Court)
def create_court(court: CourtCreate, session: Session = Depends(get_session)):
    """Create a new court."""
    db_court = Court.model_validate(court)
    session.add(db_court)
    session.commit()
    session.refresh(db_court)
    return db_court


@app.get("/courts/", response_model=List[Court])
def list_courts(
    skip: int = 0, limit: int = 10, session: Session = Depends(get_session)
):
    """List all courts with pagination."""
    courts = session.exec(select(Court).offset(skip).limit(limit)).all()
    return courts


@app.get("/courts/{court_id}", response_model=Court)
def get_court(court_id: int, session: Session = Depends(get_session)):
    """Get a specific court by ID."""
    court = session.get(Court, court_id)
    if not court:
        raise HTTPException(status_code=404, detail="Court not found")
    return court


@app.patch("/courts/{court_id}", response_model=Court)
def update_court(
    court_id: int, court_update: CourtUpdate, session: Session = Depends(get_session)
):
    """Update specific fields of a court."""
    db_court = session.get(Court, court_id)
    if not db_court:
        raise HTTPException(status_code=404, detail="Court not found")
    
    court_data = court_update.model_dump(exclude_unset=True)
    for key, value in court_data.items():
        setattr(db_court, key, value)
    
    session.add(db_court)
    session.commit()
    session.refresh(db_court)
    return db_court


@app.delete("/courts/{court_id}")
def delete_court(
    court_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """Delete a court."""
    db_court = session.get(Court, court_id)
    if not db_court:
        raise HTTPException(status_code=404, detail="Court not found")

    if len(db_court.games) > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete court with active games. Delete the games first."
        )

    session.delete(db_court)
    session.commit()
    return {"ok": True}

# ============== PLAYER CRUD ROUTES ==============
@app.post("/players/", response_model=Player)
def create_player(player: PlayerCreate, session: Session = Depends(get_session)):
    """Create a new player."""
    db_player = Player.model_validate(player)
    session.add(db_player)
    session.commit()
    session.refresh(db_player)
    return db_player


@app.get("/players/", response_model=List[Player])
def list_players(
    skip: int = 0, limit: int = 10, session: Session = Depends(get_session)
):
    """List players with pagination."""
    players = session.exec(select(Player).offset(skip).limit(limit)).all()
    return players


@app.get("/players/{player_id}", response_model=Player)
def get_player(player_id: int, session: Session = Depends(get_session)):
    """Get a specific player by ID."""
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@app.patch("/players/{player_id}", response_model=Player)
def update_player(
    player_id: int, player_update: PlayerUpdate, session: Session = Depends(get_session)
):
    """Update specific fields of a player."""
    db_player = session.get(Player, player_id)
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")

    player_data = player_update.model_dump(exclude_unset=True)
    for key, value in player_data.items():
        setattr(db_player, key, value)

    session.add(db_player)
    session.commit()
    session.refresh(db_player)
    return db_player


@app.delete("/players/{player_id}")
def delete_player(
    player_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """Delete a player."""
    db_player = session.get(Player, player_id)
    if not db_player:
        raise HTTPException(status_code=404, detail="Player not found")

    session.delete(db_player)
    session.commit()
    return {"ok": True}


# ============== GAME CRUD ROUTES ==============

@app.post("/games/", response_model=Game)
def create_game(game: GameCreate, session: Session = Depends(get_session)):
    """Create a new game."""
    db_game = Game.model_validate(game)
    session.add(db_game)
    session.commit()
    session.refresh(db_game)
    return db_game


@app.get("/games/", response_model=List[GameRead])
def list_games(
    skip: int = 0, limit: int = 10, session: Session = Depends(get_session)
):
    """List games with pagination."""
    games = session.exec(
        select(Game)
        .options(selectinload(Game.players))
        .offset(skip)
        .limit(limit)
    ).all()
    return games


@app.get("/games/{game_id}", response_model=GameRead)
def get_game(game_id: int, session: Session = Depends(get_session)):
    """Get a specific game by ID."""
    game = session.exec(
        select(Game)
        .where(Game.id == game_id)
        .options(selectinload(Game.players))
    ).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@app.patch("/games/{game_id}", response_model=Game)
def update_game(
    game_id: int, game_update: GameUpdate, session: Session = Depends(get_session)
):
    """Update specific fields of a game."""
    db_game = session.get(Game, game_id)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    game_data = game_update.model_dump(exclude_unset=True)
    for key, value in game_data.items():
        setattr(db_game, key, value)

    session.add(db_game)
    session.commit()
    session.refresh(db_game)
    return db_game


@app.delete("/games/{game_id}")
def delete_game(
    game_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """Delete a game."""
    db_game = session.get(Game, game_id)
    if not db_game:
        raise HTTPException(status_code=404, detail="Game not found")

    db_game.players = []
    session.add(db_game)

    session.delete(db_game)
    session.commit()
    return {"ok": True}


@app.post("/games/{game_id}/players/{player_id}", response_model=GameRead)
def add_player_to_game(
    game_id: int, player_id: int, session: Session = Depends(get_session)
):
    """Register a player to a game."""
    game = session.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if any(existing_player.id == player_id for existing_player in game.players):
        raise HTTPException(
            status_code=400,
            detail="Player is already registered for this game",
        )

    game.players.append(player)

    session.add(game)
    session.commit()
    refreshed_game = session.exec(
        select(Game)
        .where(Game.id == game_id)
        .options(selectinload(Game.players))
    ).first()
    return refreshed_game
