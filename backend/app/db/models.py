from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, Index, Text, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"

    id = Column(String, primary_key=True)  # Cricsheet match ID or identifier
    season = Column(String, index=True)
    date = Column(String, index=True)
    match_type = Column(String, index=True)  # T20, ODI, Test, IT20, etc.
    gender = Column(String, default="male")
    venue = Column(String, index=True)
    city = Column(String, nullable=True)
    team1 = Column(String, index=True)
    team2 = Column(String, index=True)
    toss_winner = Column(String, nullable=True)
    toss_decision = Column(String, nullable=True)
    winner = Column(String, index=True, nullable=True)
    win_by_runs = Column(Integer, default=0)
    win_by_wickets = Column(Integer, default=0)
    outcome_result = Column(String, default="normal")
    player_of_match = Column(String, index=True, nullable=True)
    overs_limit = Column(Integer, default=20)
    event_name = Column(String, nullable=True)
    match_number = Column(Integer, nullable=True)
    data_version = Column(String, nullable=True)
    created_date = Column(String, nullable=True)
    source_file = Column(String, nullable=True)

    deliveries = relationship("Delivery", back_populates="match", cascade="all, delete-orphan")


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.id", ondelete="CASCADE"), index=True)
    inning = Column(Integer, index=True)
    batting_team = Column(String, index=True)
    bowling_team = Column(String, index=True)
    over = Column(Integer, index=True)
    ball = Column(Integer)
    batter = Column(String, index=True)
    batter_id = Column(String, index=True, nullable=True)
    bowler = Column(String, index=True)
    bowler_id = Column(String, index=True, nullable=True)
    non_striker = Column(String, nullable=True)
    non_striker_id = Column(String, nullable=True)
    batsman_runs = Column(Integer, default=0)
    extra_runs = Column(Integer, default=0)
    total_runs = Column(Integer, default=0)
    extras_type = Column(String, nullable=True)
    is_wicket = Column(Boolean, default=False, index=True)
    dismissed_player = Column(String, nullable=True)
    dismissal_kind = Column(String, nullable=True)
    fielder = Column(String, nullable=True)
    is_boundary = Column(Boolean, default=False)
    is_six = Column(Boolean, default=False)

    match = relationship("Match", back_populates="deliveries")

    __table_args__ = (
        UniqueConstraint("match_id", "inning", "over", "ball", name="uq_delivery_ball"),
        Index("idx_batter_bowler", "batter", "bowler"),
        Index("idx_match_inning_over", "match_id", "inning", "over"),
        Index("idx_batter_phase", "batter", "over"),
        Index("idx_bowler_phase", "bowler", "over"),
    )


class Player(Base):
    __tablename__ = "players"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, index=True)
    cricsheet_id = Column(String, index=True, nullable=True)
    country = Column(String, index=True, nullable=True)
    batting_style = Column(String, nullable=True)
    bowling_style = Column(String, nullable=True)
    role = Column(String, nullable=True)  # Batter, Bowler, All-rounder, Wicketkeeper


class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, index=True)
    short_code = Column(String, index=True, nullable=True)
