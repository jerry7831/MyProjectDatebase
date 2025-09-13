"""
国际象棋比赛数据模型 - Python ORM实现
使用SQLAlchemy进行数据库操作
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, Decimal, Enum, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime, date
from typing import List, Optional
import enum

Base = declarative_base()

# 枚举类定义
class GenderEnum(enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"

class MembershipTypeEnum(enum.Enum):
    REGULAR = "Regular"
    PREMIUM = "Premium"
    HONORARY = "Honorary"

class MembershipStatusEnum(enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"

class SponsorTypeEnum(enum.Enum):
    CORPORATE = "Corporate"
    GOVERNMENT = "Government"
    INDIVIDUAL = "Individual"
    ORGANIZATION = "Organization"

class TournamentTypeEnum(enum.Enum):
    SWISS = "Swiss"
    ROUND_ROBIN = "Round Robin"
    KNOCKOUT = "Knockout"
    ARENA = "Arena"

class TournamentStatusEnum(enum.Enum):
    PLANNED = "Planned"
    REGISTRATION_OPEN = "Registration Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class ParticipantStatusEnum(enum.Enum):
    REGISTERED = "Registered"
    CONFIRMED = "Confirmed"
    WITHDRAWN = "Withdrawn"
    DISQUALIFIED = "Disqualified"

class MatchResultEnum(enum.Enum):
    WHITE_WINS = "1-0"
    BLACK_WINS = "0-1"
    DRAW = "1/2-1/2"
    UNFINISHED = "*"

class MatchStatusEnum(enum.Enum):
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    POSTPONED = "Postponed"
    FORFEITED = "Forfeited"

class SponsorshipTypeEnum(enum.Enum):
    TITLE = "Title"
    MAIN = "Main"
    SUPPORTING = "Supporting"
    MEDIA = "Media"


# 1. 俱乐部模型
class Club(Base):
    __tablename__ = 'clubs'
    
    club_id = Column(Integer, primary_key=True, autoincrement=True)
    club_name = Column(String(100), nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    established_date = Column(Date)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    members = relationship("Member", back_populates="club")
    hosted_tournaments = relationship("Tournament", back_populates="hosting_club")
    
    def __repr__(self):
        return f"<Club(id={self.club_id}, name='{self.club_name}')>"


# 2. 棋手模型
class Player(Base):
    __tablename__ = 'players'
    
    player_id = Column(Integer, primary_key=True, autoincrement=True)
    player_name = Column(String(100), nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    birth_date = Column(Date)
    nationality = Column(String(50))
    gender = Column(Enum(GenderEnum))
    rating = Column(Integer, default=1200)  # 国际象棋等级分
    title = Column(String(20))  # 如GM(特级大师), IM(国际大师)等
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    memberships = relationship("Member", back_populates="player")
    tournament_participations = relationship("TournamentParticipant", back_populates="player")
    white_matches = relationship("Match", foreign_keys="Match.white_player_id", back_populates="white_player")
    black_matches = relationship("Match", foreign_keys="Match.black_player_id", back_populates="black_player")
    rankings = relationship("PlayerRanking", back_populates="player")
    tournament_standings = relationship("TournamentStanding", back_populates="player")
    
    def __repr__(self):
        return f"<Player(id={self.player_id}, name='{self.player_name}', rating={self.rating})>"
    
    @property
    def current_club(self):
        """获取当前所属俱乐部"""
        active_membership = next((m for m in self.memberships if m.status == MembershipStatusEnum.ACTIVE), None)
        return active_membership.club if active_membership else None


# 3. 会员模型
class Member(Base):
    __tablename__ = 'members'
    
    membership_id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.player_id', ondelete='CASCADE'), nullable=False)
    club_id = Column(Integer, ForeignKey('clubs.club_id', ondelete='CASCADE'), nullable=False)
    join_date = Column(Date, nullable=False)
    membership_type = Column(Enum(MembershipTypeEnum), default=MembershipTypeEnum.REGULAR)
    status = Column(Enum(MembershipStatusEnum), default=MembershipStatusEnum.ACTIVE)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    player = relationship("Player", back_populates="memberships")
    club = relationship("Club", back_populates="members")
    
    # 约束：确保一个棋手在任何时候只能是一个俱乐部的活跃会员
    __table_args__ = (
        Index('idx_members_player_status', 'player_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Member(id={self.membership_id}, player='{self.player.player_name}', club='{self.club.club_name}')>"


# 4. 赞助商模型
class Sponsor(Base):
    __tablename__ = 'sponsors'
    
    sponsor_id = Column(Integer, primary_key=True, autoincrement=True)
    sponsor_name = Column(String(100), nullable=False)
    sponsor_type = Column(Enum(SponsorTypeEnum), nullable=False)
    contact_person = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    website = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    
    # 关系
    tournament_sponsorships = relationship("TournamentSponsor", back_populates="sponsor")
    
    def __repr__(self):
        return f"<Sponsor(id={self.sponsor_id}, name='{self.sponsor_name}')>"


# 5. 锦标赛模型
class Tournament(Base):
    __tablename__ = 'tournaments'
    
    tournament_id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_code = Column(String(20), unique=True, nullable=False)
    tournament_name = Column(String(150), nullable=False)
    hosting_club_id = Column(Integer, ForeignKey('clubs.club_id', ondelete='SET NULL'))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    location = Column(String(200))
    entry_fee = Column(Decimal(10, 2), default=0.00)
    prize_pool = Column(Decimal(12, 2), default=0.00)
    max_participants = Column(Integer, default=100)
    tournament_type = Column(Enum(TournamentTypeEnum), default=TournamentTypeEnum.SWISS)
    time_control = Column(String(50))  # 如 "90+30" (90分钟+30秒)
    status = Column(Enum(TournamentStatusEnum), default=TournamentStatusEnum.PLANNED)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    hosting_club = relationship("Club", back_populates="hosted_tournaments")
    participants = relationship("TournamentParticipant", back_populates="tournament")
    matches = relationship("Match", back_populates="tournament")
    sponsorships = relationship("TournamentSponsor", back_populates="tournament")
    standings = relationship("TournamentStanding", back_populates="tournament")
    
    # 约束
    __table_args__ = (
        CheckConstraint('end_date >= start_date', name='check_tournament_dates'),
        Index('idx_tournaments_dates', 'start_date', 'end_date'),
    )
    
    def __repr__(self):
        return f"<Tournament(id={self.tournament_id}, code='{self.tournament_code}', name='{self.tournament_name}')>"
    
    @property
    def participant_count(self):
        """获取参赛人数"""
        return len([p for p in self.participants if p.status in [ParticipantStatusEnum.REGISTERED, ParticipantStatusEnum.CONFIRMED]])


# 6. 锦标赛赞助关系模型
class TournamentSponsor(Base):
    __tablename__ = 'tournament_sponsors'
    
    tournament_id = Column(Integer, ForeignKey('tournaments.tournament_id', ondelete='CASCADE'), primary_key=True)
    sponsor_id = Column(Integer, ForeignKey('sponsors.sponsor_id', ondelete='CASCADE'), primary_key=True)
    sponsorship_amount = Column(Decimal(10, 2), default=0.00)
    sponsorship_type = Column(Enum(SponsorshipTypeEnum), default=SponsorshipTypeEnum.SUPPORTING)
    contract_date = Column(Date)
    
    # 关系
    tournament = relationship("Tournament", back_populates="sponsorships")
    sponsor = relationship("Sponsor", back_populates="tournament_sponsorships")
    
    def __repr__(self):
        return f"<TournamentSponsor(tournament='{self.tournament.tournament_name}', sponsor='{self.sponsor.sponsor_name}')>"


# 7. 锦标赛参赛者模型
class TournamentParticipant(Base):
    __tablename__ = 'tournament_participants'
    
    tournament_id = Column(Integer, ForeignKey('tournaments.tournament_id', ondelete='CASCADE'), primary_key=True)
    player_id = Column(Integer, ForeignKey('players.player_id', ondelete='CASCADE'), primary_key=True)
    registration_date = Column(DateTime, default=func.now())
    seed_number = Column(Integer)  # 种子排名
    initial_rating = Column(Integer)  # 参赛时的等级分
    status = Column(Enum(ParticipantStatusEnum), default=ParticipantStatusEnum.REGISTERED)
    
    # 关系
    tournament = relationship("Tournament", back_populates="participants")
    player = relationship("Player", back_populates="tournament_participations")
    
    def __repr__(self):
        return f"<TournamentParticipant(tournament='{self.tournament.tournament_name}', player='{self.player.player_name}')>"


# 8. 比赛模型
class Match(Base):
    __tablename__ = 'matches'
    
    match_id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.tournament_id', ondelete='CASCADE'), nullable=False)
    round_number = Column(Integer, nullable=False)
    board_number = Column(Integer)  # 台次号
    white_player_id = Column(Integer, ForeignKey('players.player_id', ondelete='CASCADE'), nullable=False)
    black_player_id = Column(Integer, ForeignKey('players.player_id', ondelete='CASCADE'), nullable=False)
    scheduled_time = Column(DateTime)
    actual_start_time = Column(DateTime)
    actual_end_time = Column(DateTime)
    result = Column(Enum(MatchResultEnum), default=MatchResultEnum.UNFINISHED)
    moves_pgn = Column(Text)  # PGN格式的棋谱
    time_control_used = Column(String(50))
    arbiter = Column(String(100))  # 裁判
    status = Column(Enum(MatchStatusEnum), default=MatchStatusEnum.SCHEDULED)
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    tournament = relationship("Tournament", back_populates="matches")
    white_player = relationship("Player", foreign_keys=[white_player_id], back_populates="white_matches")
    black_player = relationship("Player", foreign_keys=[black_player_id], back_populates="black_matches")
    
    # 约束
    __table_args__ = (
        CheckConstraint('white_player_id != black_player_id', name='check_different_players'),
        CheckConstraint('actual_end_time IS NULL OR actual_start_time IS NULL OR actual_end_time >= actual_start_time', name='check_match_times'),
        Index('idx_matches_tournament_round', 'tournament_id', 'round_number'),
        Index('idx_matches_players', 'white_player_id', 'black_player_id'),
    )
    
    def __repr__(self):
        return f"<Match(id={self.match_id}, white='{self.white_player.player_name}' vs black='{self.black_player.player_name}', result='{self.result}')>"
    
    def get_result_for_player(self, player_id: int) -> float:
        """获取指定棋手在此比赛中的得分"""
        if self.result == MatchResultEnum.UNFINISHED:
            return 0.0
        elif self.result == MatchResultEnum.DRAW:
            return 0.5
        elif self.result == MatchResultEnum.WHITE_WINS:
            return 1.0 if player_id == self.white_player_id else 0.0
        elif self.result == MatchResultEnum.BLACK_WINS:
            return 1.0 if player_id == self.black_player_id else 0.0
        return 0.0


# 9. 棋手排名历史模型
class PlayerRanking(Base):
    __tablename__ = 'player_rankings'
    
    ranking_id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.player_id', ondelete='CASCADE'), nullable=False)
    rating = Column(Integer, nullable=False)
    ranking_date = Column(Date, nullable=False)
    tournament_id = Column(Integer, ForeignKey('tournaments.tournament_id', ondelete='SET NULL'))
    rating_change = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    
    # 关系
    player = relationship("Player", back_populates="rankings")
    tournament = relationship("Tournament")
    
    # 约束
    __table_args__ = (
        UniqueConstraint('player_id', 'ranking_date', name='unique_player_date'),
        Index('idx_rankings_player_date', 'player_id', 'ranking_date'),
    )
    
    def __repr__(self):
        return f"<PlayerRanking(player='{self.player.player_name}', rating={self.rating}, date='{self.ranking_date}')>"


# 10. 锦标赛排行榜模型
class TournamentStanding(Base):
    __tablename__ = 'tournament_standings'
    
    tournament_id = Column(Integer, ForeignKey('tournaments.tournament_id', ondelete='CASCADE'), primary_key=True)
    player_id = Column(Integer, ForeignKey('players.player_id', ondelete='CASCADE'), primary_key=True)
    points = Column(Decimal(3, 1), default=0.0)  # 积分（胜1分，和0.5分，负0分）
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    buchholz_score = Column(Decimal(5, 1), default=0.0)  # 布赫霍尔兹分数
    sonneborn_berger = Column(Decimal(5, 1), default=0.0)  # 索纳博恩-贝格尔分数
    final_rank = Column(Integer)
    prize_amount = Column(Decimal(10, 2), default=0.00)
    
    # 关系
    tournament = relationship("Tournament", back_populates="standings")
    player = relationship("Player", back_populates="tournament_standings")
    
    # 索引
    __table_args__ = (
        Index('idx_standings_tournament_points', 'tournament_id', 'points'),
    )
    
    def __repr__(self):
        return f"<TournamentStanding(tournament='{self.tournament.tournament_name}', player='{self.player.player_name}', points={self.points})>"


# 数据库连接和会话管理
class ChessDatabase:
    def __init__(self, database_url: str = "sqlite:///chess_tournament.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def drop_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(bind=self.engine)


# 示例使用
if __name__ == "__main__":
    # 创建数据库实例
    db = ChessDatabase()
    
    # 创建所有表
    db.create_tables()
    
    # 获取会话
    session = db.get_session()
    
    try:
        # 创建示例数据
        # 俱乐部
        club1 = Club(
            club_name="北京国际象棋俱乐部",
            address="北京市朝阳区某街道123号",
            phone="010-12345678",
            email="beijing@chess.com",
            established_date=date(2010, 1, 15)
        )
        
        club2 = Club(
            club_name="上海国际象棋俱乐部",
            address="上海市浦东新区某路456号",
            phone="021-87654321",
            email="shanghai@chess.com",
            established_date=date(2008, 3, 20)
        )
        
        session.add_all([club1, club2])
        session.commit()
        
        # 棋手
        player1 = Player(
            player_name="张伟",
            address="北京市某区某街1号",
            phone="13800000001",
            email="zhangwei@email.com",
            birth_date=date(1990, 5, 15),
            nationality="Chinese",
            gender=GenderEnum.MALE,
            rating=2200,
            title="FM"
        )
        
        player2 = Player(
            player_name="李娜",
            address="上海市某区某路2号",
            phone="13800000002",
            email="lina@email.com",
            birth_date=date(1992, 8, 20),
            nationality="Chinese",
            gender=GenderEnum.FEMALE,
            rating=2100,
            title="WFM"
        )
        
        session.add_all([player1, player2])
        session.commit()
        
        # 会员关系
        member1 = Member(
            player_id=player1.player_id,
            club_id=club1.club_id,
            join_date=date(2023, 1, 1),
            membership_type=MembershipTypeEnum.PREMIUM,
            status=MembershipStatusEnum.ACTIVE
        )
        
        member2 = Member(
            player_id=player2.player_id,
            club_id=club2.club_id,
            join_date=date(2023, 2, 15),
            membership_type=MembershipTypeEnum.REGULAR,
            status=MembershipStatusEnum.ACTIVE
        )
        
        session.add_all([member1, member2])
        session.commit()
        
        # 锦标赛
        tournament = Tournament(
            tournament_code="BJOPEN2024",
            tournament_name="2024北京公开赛",
            hosting_club_id=club1.club_id,
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 7),
            location="北京市国际会议中心",
            entry_fee=200.00,
            prize_pool=50000.00,
            max_participants=100,
            tournament_type=TournamentTypeEnum.SWISS,
            time_control="90+30",
            status=TournamentStatusEnum.PLANNED
        )
        
        session.add(tournament)
        session.commit()
        
        print("示例数据创建成功！")
        print(f"俱乐部数量: {session.query(Club).count()}")
        print(f"棋手数量: {session.query(Player).count()}")
        print(f"会员数量: {session.query(Member).count()}")
        print(f"锦标赛数量: {session.query(Tournament).count()}")
        
    except Exception as e:
        session.rollback()
        print(f"创建示例数据时出错: {e}")
    finally:
        session.close()
