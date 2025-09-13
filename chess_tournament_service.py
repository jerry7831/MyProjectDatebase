"""
国际象棋比赛数据模型 - 业务逻辑服务层
提供常用的数据库操作和查询功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from chess_tournament_models import (
    ChessDatabase, Club, Player, Member, Tournament, Match, 
    TournamentParticipant, TournamentStanding, PlayerRanking,
    Sponsor, TournamentSponsor,
    MembershipStatusEnum, TournamentStatusEnum, MatchResultEnum,
    ParticipantStatusEnum, MatchStatusEnum
)
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func


class ChessTournamentService:
    """国际象棋比赛管理服务类"""
    
    def __init__(self, database_url: str = "sqlite:///chess_tournament.db"):
        self.db = ChessDatabase(database_url)
        self.db.create_tables()
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.db.get_session()
    
    # ============= 俱乐部管理 =============
    
    def create_club(self, name: str, address: str = None, phone: str = None, 
                   email: str = None, established_date: date = None, 
                   description: str = None) -> Club:
        """创建新俱乐部"""
        session = self.get_session()
        try:
            club = Club(
                club_name=name,
                address=address,
                phone=phone,
                email=email,
                established_date=established_date,
                description=description
            )
            session.add(club)
            session.commit()
            session.refresh(club)
            return club
        finally:
            session.close()
    
    def get_club_by_id(self, club_id: int) -> Optional[Club]:
        """根据ID获取俱乐部"""
        session = self.get_session()
        try:
            return session.query(Club).filter(Club.club_id == club_id).first()
        finally:
            session.close()
    
    def get_all_clubs(self) -> List[Club]:
        """获取所有俱乐部"""
        session = self.get_session()
        try:
            return session.query(Club).all()
        finally:
            session.close()
    
    def get_club_members(self, club_id: int, active_only: bool = True) -> List[Member]:
        """获取俱乐部成员"""
        session = self.get_session()
        try:
            query = session.query(Member).filter(Member.club_id == club_id)
            if active_only:
                query = query.filter(Member.status == MembershipStatusEnum.ACTIVE)
            return query.all()
        finally:
            session.close()
    
    # ============= 棋手管理 =============
    
    def create_player(self, name: str, address: str = None, phone: str = None,
                     email: str = None, birth_date: date = None, 
                     nationality: str = None, gender = None, 
                     rating: int = 1200, title: str = None) -> Player:
        """创建新棋手"""
        session = self.get_session()
        try:
            player = Player(
                player_name=name,
                address=address,
                phone=phone,
                email=email,
                birth_date=birth_date,
                nationality=nationality,
                gender=gender,
                rating=rating,
                title=title
            )
            session.add(player)
            session.commit()
            session.refresh(player)
            return player
        finally:
            session.close()
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """根据ID获取棋手"""
        session = self.get_session()
        try:
            return session.query(Player).filter(Player.player_id == player_id).first()
        finally:
            session.close()
    
    def search_players(self, name: str = None, rating_min: int = None, 
                      rating_max: int = None, title: str = None) -> List[Player]:
        """搜索棋手"""
        session = self.get_session()
        try:
            query = session.query(Player)
            if name:
                query = query.filter(Player.player_name.like(f'%{name}%'))
            if rating_min:
                query = query.filter(Player.rating >= rating_min)
            if rating_max:
                query = query.filter(Player.rating <= rating_max)
            if title:
                query = query.filter(Player.title == title)
            return query.all()
        finally:
            session.close()
    
    def get_top_players(self, limit: int = 10) -> List[Player]:
        """获取等级分最高的棋手"""
        session = self.get_session()
        try:
            return session.query(Player).order_by(desc(Player.rating)).limit(limit).all()
        finally:
            session.close()
    
    # ============= 会员管理 =============
    
    def add_member_to_club(self, player_id: int, club_id: int, 
                          membership_type = None, join_date: date = None) -> Member:
        """将棋手加入俱乐部"""
        session = self.get_session()
        try:
            # 检查是否已有活跃会员资格
            existing_active = session.query(Member).filter(
                and_(Member.player_id == player_id, 
                     Member.status == MembershipStatusEnum.ACTIVE)
            ).first()
            
            if existing_active:
                raise ValueError("该棋手已经是其他俱乐部的活跃会员")
            
            member = Member(
                player_id=player_id,
                club_id=club_id,
                join_date=join_date or date.today(),
                membership_type=membership_type,
                status=MembershipStatusEnum.ACTIVE
            )
            session.add(member)
            session.commit()
            session.refresh(member)
            return member
        finally:
            session.close()
    
    def transfer_member(self, player_id: int, new_club_id: int) -> Member:
        """转会：将棋手转移到新俱乐部"""
        session = self.get_session()
        try:
            # 将当前活跃会员资格设为非活跃
            current_membership = session.query(Member).filter(
                and_(Member.player_id == player_id,
                     Member.status == MembershipStatusEnum.ACTIVE)
            ).first()
            
            if current_membership:
                current_membership.status = MembershipStatusEnum.INACTIVE
            
            # 创建新的会员资格
            new_member = Member(
                player_id=player_id,
                club_id=new_club_id,
                join_date=date.today(),
                status=MembershipStatusEnum.ACTIVE
            )
            session.add(new_member)
            session.commit()
            session.refresh(new_member)
            return new_member
        finally:
            session.close()
    
    # ============= 锦标赛管理 =============
    
    def create_tournament(self, code: str, name: str, start_date: date, 
                         end_date: date, hosting_club_id: int = None,
                         location: str = None, entry_fee: Decimal = Decimal('0.00'),
                         prize_pool: Decimal = Decimal('0.00'), 
                         max_participants: int = 100, tournament_type = None,
                         time_control: str = None) -> Tournament:
        """创建新锦标赛"""
        session = self.get_session()
        try:
            tournament = Tournament(
                tournament_code=code,
                tournament_name=name,
                hosting_club_id=hosting_club_id,
                start_date=start_date,
                end_date=end_date,
                location=location,
                entry_fee=entry_fee,
                prize_pool=prize_pool,
                max_participants=max_participants,
                tournament_type=tournament_type,
                time_control=time_control,
                status=TournamentStatusEnum.PLANNED
            )
            session.add(tournament)
            session.commit()
            session.refresh(tournament)
            return tournament
        finally:
            session.close()
    
    def get_tournament_by_code(self, code: str) -> Optional[Tournament]:
        """根据代码获取锦标赛"""
        session = self.get_session()
        try:
            return session.query(Tournament).filter(Tournament.tournament_code == code).first()
        finally:
            session.close()
    
    def get_upcoming_tournaments(self, limit: int = 10) -> List[Tournament]:
        """获取即将开始的锦标赛"""
        session = self.get_session()
        try:
            return session.query(Tournament).filter(
                Tournament.start_date >= date.today()
            ).order_by(Tournament.start_date).limit(limit).all()
        finally:
            session.close()
    
    def get_tournaments_by_year(self, year: int) -> List[Tournament]:
        """获取指定年份的锦标赛"""
        session = self.get_session()
        try:
            start_of_year = date(year, 1, 1)
            end_of_year = date(year, 12, 31)
            return session.query(Tournament).filter(
                and_(Tournament.start_date >= start_of_year,
                     Tournament.start_date <= end_of_year)
            ).order_by(Tournament.start_date).all()
        finally:
            session.close()
    
    # ============= 参赛管理 =============
    
    def register_player_for_tournament(self, tournament_id: int, player_id: int,
                                     seed_number: int = None) -> TournamentParticipant:
        """为锦标赛注册棋手"""
        session = self.get_session()
        try:
            # 检查是否已经注册
            existing = session.query(TournamentParticipant).filter(
                and_(TournamentParticipant.tournament_id == tournament_id,
                     TournamentParticipant.player_id == player_id)
            ).first()
            
            if existing:
                raise ValueError("该棋手已经注册了这个锦标赛")
            
            # 获取棋手当前等级分
            player = session.query(Player).filter(Player.player_id == player_id).first()
            if not player:
                raise ValueError("棋手不存在")
            
            participant = TournamentParticipant(
                tournament_id=tournament_id,
                player_id=player_id,
                seed_number=seed_number,
                initial_rating=player.rating,
                status=ParticipantStatusEnum.REGISTERED
            )
            session.add(participant)
            session.commit()
            session.refresh(participant)
            return participant
        finally:
            session.close()
    
    def get_tournament_participants(self, tournament_id: int, 
                                  confirmed_only: bool = False) -> List[TournamentParticipant]:
        """获取锦标赛参赛者"""
        session = self.get_session()
        try:
            query = session.query(TournamentParticipant).filter(
                TournamentParticipant.tournament_id == tournament_id
            )
            if confirmed_only:
                query = query.filter(TournamentParticipant.status == ParticipantStatusEnum.CONFIRMED)
            return query.order_by(TournamentParticipant.seed_number).all()
        finally:
            session.close()
    
    # ============= 比赛管理 =============
    
    def create_match(self, tournament_id: int, round_number: int,
                    white_player_id: int, black_player_id: int,
                    board_number: int = None, scheduled_time: datetime = None) -> Match:
        """创建比赛"""
        session = self.get_session()
        try:
            match = Match(
                tournament_id=tournament_id,
                round_number=round_number,
                board_number=board_number,
                white_player_id=white_player_id,
                black_player_id=black_player_id,
                scheduled_time=scheduled_time,
                status=MatchStatusEnum.SCHEDULED
            )
            session.add(match)
            session.commit()
            session.refresh(match)
            return match
        finally:
            session.close()
    
    def update_match_result(self, match_id: int, result: MatchResultEnum,
                           moves_pgn: str = None, actual_start_time: datetime = None,
                           actual_end_time: datetime = None) -> Match:
        """更新比赛结果"""
        session = self.get_session()
        try:
            match = session.query(Match).filter(Match.match_id == match_id).first()
            if not match:
                raise ValueError("比赛不存在")
            
            match.result = result
            match.status = MatchStatusEnum.COMPLETED
            if moves_pgn:
                match.moves_pgn = moves_pgn
            if actual_start_time:
                match.actual_start_time = actual_start_time
            if actual_end_time:
                match.actual_end_time = actual_end_time
            
            session.commit()
            session.refresh(match)
            
            # 更新积分榜
            self._update_tournament_standings(session, match.tournament_id)
            
            return match
        finally:
            session.close()
    
    def get_tournament_matches(self, tournament_id: int, 
                              round_number: int = None) -> List[Match]:
        """获取锦标赛的比赛"""
        session = self.get_session()
        try:
            query = session.query(Match).filter(Match.tournament_id == tournament_id)
            if round_number:
                query = query.filter(Match.round_number == round_number)
            return query.order_by(Match.round_number, Match.board_number).all()
        finally:
            session.close()
    
    def get_player_matches(self, player_id: int, tournament_id: int = None) -> List[Match]:
        """获取棋手的比赛"""
        session = self.get_session()
        try:
            query = session.query(Match).filter(
                or_(Match.white_player_id == player_id, 
                    Match.black_player_id == player_id)
            )
            if tournament_id:
                query = query.filter(Match.tournament_id == tournament_id)
            return query.order_by(desc(Match.scheduled_time)).all()
        finally:
            session.close()
    
    # ============= 积分和排名管理 =============
    
    def _update_tournament_standings(self, session: Session, tournament_id: int):
        """更新锦标赛积分榜"""
        # 获取所有参赛者
        participants = session.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id
        ).all()
        
        for participant in participants:
            player_id = participant.player_id
            
            # 获取该棋手的所有已完成比赛
            matches = session.query(Match).filter(
                and_(Match.tournament_id == tournament_id,
                     or_(Match.white_player_id == player_id, 
                         Match.black_player_id == player_id),
                     Match.status == MatchStatusEnum.COMPLETED)
            ).all()
            
            # 计算积分统计
            points = 0.0
            wins = 0
            draws = 0
            losses = 0
            
            for match in matches:
                result = match.get_result_for_player(player_id)
                points += result
                
                if result == 1.0:
                    wins += 1
                elif result == 0.5:
                    draws += 1
                elif result == 0.0:
                    losses += 1
            
            # 更新或创建积分榜记录
            standing = session.query(TournamentStanding).filter(
                and_(TournamentStanding.tournament_id == tournament_id,
                     TournamentStanding.player_id == player_id)
            ).first()
            
            if not standing:
                standing = TournamentStanding(
                    tournament_id=tournament_id,
                    player_id=player_id
                )
                session.add(standing)
            
            standing.points = Decimal(str(points))
            standing.games_played = len(matches)
            standing.wins = wins
            standing.draws = draws
            standing.losses = losses
        
        session.commit()
    
    def get_tournament_standings(self, tournament_id: int) -> List[TournamentStanding]:
        """获取锦标赛积分榜"""
        session = self.get_session()
        try:
            return session.query(TournamentStanding).filter(
                TournamentStanding.tournament_id == tournament_id
            ).order_by(desc(TournamentStanding.points), 
                      desc(TournamentStanding.buchholz_score)).all()
        finally:
            session.close()
    
    def update_player_rating(self, player_id: int, new_rating: int, 
                           tournament_id: int = None, rating_change: int = 0) -> PlayerRanking:
        """更新棋手等级分"""
        session = self.get_session()
        try:
            # 更新棋手表中的等级分
            player = session.query(Player).filter(Player.player_id == player_id).first()
            if not player:
                raise ValueError("棋手不存在")
            
            old_rating = player.rating
            player.rating = new_rating
            
            # 记录等级分历史
            ranking = PlayerRanking(
                player_id=player_id,
                rating=new_rating,
                ranking_date=date.today(),
                tournament_id=tournament_id,
                rating_change=rating_change or (new_rating - old_rating)
            )
            session.add(ranking)
            session.commit()
            session.refresh(ranking)
            return ranking
        finally:
            session.close()
    
    # ============= 统计查询 =============
    
    def get_tournament_statistics(self, tournament_id: int) -> Dict[str, Any]:
        """获取锦标赛统计信息"""
        session = self.get_session()
        try:
            tournament = session.query(Tournament).filter(
                Tournament.tournament_id == tournament_id
            ).first()
            
            if not tournament:
                return {}
            
            # 参赛人数
            participant_count = session.query(TournamentParticipant).filter(
                TournamentParticipant.tournament_id == tournament_id
            ).count()
            
            # 比赛场次
            total_matches = session.query(Match).filter(
                Match.tournament_id == tournament_id
            ).count()
            
            completed_matches = session.query(Match).filter(
                and_(Match.tournament_id == tournament_id,
                     Match.status == MatchStatusEnum.COMPLETED)
            ).count()
            
            # 轮次数
            max_round = session.query(func.max(Match.round_number)).filter(
                Match.tournament_id == tournament_id
            ).scalar() or 0
            
            return {
                'tournament_name': tournament.tournament_name,
                'participant_count': participant_count,
                'total_matches': total_matches,
                'completed_matches': completed_matches,
                'progress_percentage': (completed_matches / total_matches * 100) if total_matches > 0 else 0,
                'total_rounds': max_round,
                'prize_pool': float(tournament.prize_pool),
                'status': tournament.status.value
            }
        finally:
            session.close()
    
    def get_player_statistics(self, player_id: int, year: int = None) -> Dict[str, Any]:
        """获取棋手统计信息"""
        session = self.get_session()
        try:
            player = session.query(Player).filter(Player.player_id == player_id).first()
            if not player:
                return {}
            
            # 构建查询条件
            match_query = session.query(Match).filter(
                and_(or_(Match.white_player_id == player_id, 
                        Match.black_player_id == player_id),
                     Match.status == MatchStatusEnum.COMPLETED)
            )
            
            if year:
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
                match_query = match_query.join(Tournament).filter(
                    and_(Tournament.start_date >= start_date,
                         Tournament.start_date <= end_date)
                )
            
            matches = match_query.all()
            
            # 统计胜负场次
            wins = 0
            draws = 0
            losses = 0
            total_points = 0.0
            
            for match in matches:
                result = match.get_result_for_player(player_id)
                total_points += result
                
                if result == 1.0:
                    wins += 1
                elif result == 0.5:
                    draws += 1
                elif result == 0.0:
                    losses += 1
            
            total_games = len(matches)
            win_rate = (wins / total_games * 100) if total_games > 0 else 0
            
            # 参赛锦标赛数量
            tournament_count = session.query(TournamentParticipant).filter(
                TournamentParticipant.player_id == player_id
            ).count()
            
            return {
                'player_name': player.player_name,
                'current_rating': player.rating,
                'title': player.title,
                'total_games': total_games,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'total_points': total_points,
                'win_rate': round(win_rate, 2),
                'tournaments_played': tournament_count
            }
        finally:
            session.close()


# 示例使用
if __name__ == "__main__":
    # 创建服务实例
    service = ChessTournamentService()
    
    # 创建示例数据
    try:
        # 创建俱乐部
        club1 = service.create_club("北京国际象棋俱乐部", "北京市朝阳区", "010-12345678")
        club2 = service.create_club("上海国际象棋俱乐部", "上海市浦东新区", "021-87654321")
        
        # 创建棋手
        player1 = service.create_player("张伟", rating=2200, title="FM")
        player2 = service.create_player("李娜", rating=2100, title="WFM")
        player3 = service.create_player("王强", rating=2300, title="IM")
        
        # 加入俱乐部
        service.add_member_to_club(player1.player_id, club1.club_id)
        service.add_member_to_club(player2.player_id, club2.club_id)
        service.add_member_to_club(player3.player_id, club1.club_id)
        
        # 创建锦标赛
        tournament = service.create_tournament(
            code="BJOPEN2024",
            name="2024北京公开赛",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 6, 7),
            hosting_club_id=club1.club_id,
            prize_pool=Decimal('50000.00')
        )
        
        # 注册参赛
        service.register_player_for_tournament(tournament.tournament_id, player1.player_id, seed_number=1)
        service.register_player_for_tournament(tournament.tournament_id, player2.player_id, seed_number=2)
        service.register_player_for_tournament(tournament.tournament_id, player3.player_id, seed_number=3)
        
        # 创建比赛
        match = service.create_match(
            tournament_id=tournament.tournament_id,
            round_number=1,
            white_player_id=player1.player_id,
            black_player_id=player2.player_id,
            board_number=1
        )
        
        # 更新比赛结果
        service.update_match_result(match.match_id, MatchResultEnum.WHITE_WINS)
        
        print("数据创建和操作成功！")
        
        # 查询统计信息
        tournament_stats = service.get_tournament_statistics(tournament.tournament_id)
        print(f"锦标赛统计: {tournament_stats}")
        
        player_stats = service.get_player_statistics(player1.player_id)
        print(f"棋手统计: {player_stats}")
        
        # 获取积分榜
        standings = service.get_tournament_standings(tournament.tournament_id)
        print(f"积分榜前3名:")
        for i, standing in enumerate(standings[:3], 1):
            print(f"{i}. {standing.player.player_name}: {standing.points}分")
        
    except Exception as e:
        print(f"操作过程中出错: {e}")
