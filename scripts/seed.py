"""Populate the local Pick-Up Hoops SQLite database with sample data."""

from datetime import datetime, timedelta

from sqlmodel import Session, select

from api.database import create_db_and_tables, engine
from api.auth import hash_password
from api.models import Court, Game, GameStatus, Player, SkillLevel, User


def seed_database() -> None:
    """Insert sample courts, players, and games if the database is empty."""
    create_db_and_tables()

    with Session(engine) as session:
        existing_user = session.exec(select(User)).first()
        if existing_user is None:
            users = [
                User(
                    username="admin",
                    hashed_password=hash_password("adminpassword"),
                    role="admin",
                ),
                User(
                    username="player1",
                    hashed_password=hash_password("playerpassword"),
                    role="user",
                ),
            ]
            session.add_all(users)
            session.commit()

        existing_courts = session.exec(select(Court)).first()
        if existing_courts is not None:
            print("Database already contains sample data. No new records were created.")
            return

        courts = [
            Court(
                name="Rucker Park",
                address="280 W 155th St",
                city="New York",
                num_courts=3,
                has_lighting=True,
            ),
            Court(
                name="Venice Beach Courts",
                address="1800 Ocean Front Walk",
                city="Los Angeles",
                num_courts=4,
                has_lighting=True,
            ),
            Court(
                name="Morningside Park",
                address="Morningside Dr & W 110th St",
                city="New York",
                num_courts=2,
                has_lighting=False,
            ),
        ]
        session.add_all(courts)
        session.flush()

        players = [
            Player(name="Jordan Reed", city="New York", skill_level=SkillLevel.BEGINNER),
            Player(name="Avery Chen", city="Los Angeles", skill_level=SkillLevel.INTERMEDIATE),
            Player(name="Malik Johnson", city="Chicago", skill_level=SkillLevel.ADVANCED),
            Player(name="Sam Taylor", city="Miami", skill_level=SkillLevel.INTERMEDIATE),
        ]
        session.add_all(players)
        session.flush()

        games = [
            Game(
                scheduled_time=datetime.now() + timedelta(days=2, hours=3),
                court_id=courts[0].id,
                skill_level=SkillLevel.INTERMEDIATE,
                max_players=10,
                status=GameStatus.OPEN,
            ),
            Game(
                scheduled_time=datetime.now() + timedelta(days=5, hours=1),
                court_id=courts[1].id,
                skill_level=SkillLevel.ADVANCED,
                max_players=8,
                status=GameStatus.OPEN,
            ),
        ]
        session.add_all(games)

        games[0].players.extend([players[0], players[1], players[3]])
        games[1].players.extend([players[1], players[2]])

        session.commit()

    print("Successfully created sample users, 3 courts, 4 players, and 2 games in the database.")


if __name__ == "__main__":
    seed_database()
