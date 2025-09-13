"""
国际象棋比赛数据模型 - API接口
使用FastAPI提供RESTful API服务
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import uvicorn

# Pydantic模型定义用于API请求和响应

class ClubCreate(BaseModel):
    club_name: str = Field(..., description="俱乐部名称")
    address: Optional[str] = Field(None, description="地址")
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    established_date: Optional[date] = Field(None, description="成立日期")
    description: Optional[str] = Field(None, description="描述")

class ClubResponse(BaseModel):
    club_id: int
    club_name: str
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    established_date: Optional[date]
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PlayerCreate(BaseModel):
    player_name: str = Field(..., description="棋手姓名")
    address: Optional[str] = Field(None, description="地址")
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    birth_date: Optional[date] = Field(None, description="出生日期")
    nationality: Optional[str] = Field(None, description="国籍")
    gender: Optional[str] = Field(None, description="性别")
    rating: int = Field(1200, description="等级分")
    title: Optional[str] = Field(None, description="称号")

class PlayerResponse(BaseModel):
    player_id: int
    player_name: str
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    birth_date: Optional[date]
    nationality: Optional[str]
    gender: Optional[str]
    rating: int
    title: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class TournamentCreate(BaseModel):
    tournament_code: str = Field(..., description="锦标赛代码")
    tournament_name: str = Field(..., description="锦标赛名称")
    hosting_club_id: Optional[int] = Field(None, description="主办俱乐部ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    location: Optional[str] = Field(None, description="比赛地点")
    entry_fee: Decimal = Field(Decimal('0.00'), description="报名费")
    prize_pool: Decimal = Field(Decimal('0.00'), description="奖金池")
    max_participants: int = Field(100, description="最大参赛人数")
    tournament_type: Optional[str] = Field("Swiss", description="赛制类型")
    time_control: Optional[str] = Field(None, description="时间控制")

class TournamentResponse(BaseModel):
    tournament_id: int
    tournament_code: str
    tournament_name: str
    hosting_club_id: Optional[int]
    start_date: date
    end_date: date
    location: Optional[str]
    entry_fee: Decimal
    prize_pool: Decimal
    max_participants: int
    tournament_type: Optional[str]
    time_control: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MatchCreate(BaseModel):
    tournament_id: int = Field(..., description="锦标赛ID")
    round_number: int = Field(..., description="轮次")
    white_player_id: int = Field(..., description="白棋棋手ID")
    black_player_id: int = Field(..., description="黑棋棋手ID")
    board_number: Optional[int] = Field(None, description="台次号")
    scheduled_time: Optional[datetime] = Field(None, description="预定时间")

class MatchResultUpdate(BaseModel):
    result: str = Field(..., description="比赛结果: 1-0, 0-1, 1/2-1/2, *")
    moves_pgn: Optional[str] = Field(None, description="PGN棋谱")
    actual_start_time: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(None, description="实际结束时间")

class MatchResponse(BaseModel):
    match_id: int
    tournament_id: int
    round_number: int
    board_number: Optional[int]
    white_player_id: int
    black_player_id: int
    white_player_name: str
    black_player_name: str
    scheduled_time: Optional[datetime]
    result: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TournamentRegistration(BaseModel):
    tournament_id: int = Field(..., description="锦标赛ID")
    player_id: int = Field(..., description="棋手ID")
    seed_number: Optional[int] = Field(None, description="种子排名")

class MembershipCreate(BaseModel):
    player_id: int = Field(..., description="棋手ID")
    club_id: int = Field(..., description="俱乐部ID")
    membership_type: Optional[str] = Field("Regular", description="会员类型")
    join_date: Optional[date] = Field(None, description="加入日期")

# 模拟服务层（实际使用时应该导入真实的服务类）
class MockChessTournamentService:
    """模拟的服务类，用于演示API接口"""
    
    def __init__(self):
        # 模拟数据存储
        self.clubs = {}
        self.players = {}
        self.tournaments = {}
        self.matches = {}
        self.members = {}
        self._next_id = 1
    
    def _get_next_id(self):
        self._next_id += 1
        return self._next_id - 1
    
    def create_club(self, **kwargs):
        club_id = self._get_next_id()
        club = {
            'club_id': club_id,
            'created_at': datetime.now(),
            **kwargs
        }
        self.clubs[club_id] = club
        return club
    
    def get_club_by_id(self, club_id: int):
        return self.clubs.get(club_id)
    
    def get_all_clubs(self):
        return list(self.clubs.values())
    
    def create_player(self, **kwargs):
        player_id = self._get_next_id()
        player = {
            'player_id': player_id,
            'created_at': datetime.now(),
            **kwargs
        }
        self.players[player_id] = player
        return player
    
    def get_player_by_id(self, player_id: int):
        return self.players.get(player_id)
    
    def search_players(self, **kwargs):
        return list(self.players.values())
    
    def create_tournament(self, **kwargs):
        tournament_id = self._get_next_id()
        tournament = {
            'tournament_id': tournament_id,
            'status': 'Planned',
            'created_at': datetime.now(),
            **kwargs
        }
        self.tournaments[tournament_id] = tournament
        return tournament
    
    def get_tournament_by_code(self, code: str):
        for tournament in self.tournaments.values():
            if tournament.get('tournament_code') == code:
                return tournament
        return None
    
    def get_upcoming_tournaments(self, limit: int = 10):
        return list(self.tournaments.values())[:limit]


# 创建FastAPI应用
app = FastAPI(
    title="国际象棋比赛管理系统 API",
    description="提供国际象棋比赛数据的完整管理功能",
    version="1.0.0"
)

# 创建服务实例
service = MockChessTournamentService()

# 依赖注入
def get_service():
    return service


# ============= 俱乐部管理API =============

@app.post("/clubs/", response_model=ClubResponse, tags=["俱乐部管理"])
async def create_club(club: ClubCreate, service: MockChessTournamentService = Depends(get_service)):
    """创建新俱乐部"""
    try:
        result = service.create_club(**club.dict())
        return ClubResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/clubs/{club_id}", response_model=ClubResponse, tags=["俱乐部管理"])
async def get_club(club_id: int, service: MockChessTournamentService = Depends(get_service)):
    """根据ID获取俱乐部信息"""
    club = service.get_club_by_id(club_id)
    if not club:
        raise HTTPException(status_code=404, detail="俱乐部不存在")
    return ClubResponse(**club)

@app.get("/clubs/", response_model=List[ClubResponse], tags=["俱乐部管理"])
async def list_clubs(service: MockChessTournamentService = Depends(get_service)):
    """获取所有俱乐部列表"""
    clubs = service.get_all_clubs()
    return [ClubResponse(**club) for club in clubs]


# ============= 棋手管理API =============

@app.post("/players/", response_model=PlayerResponse, tags=["棋手管理"])
async def create_player(player: PlayerCreate, service: MockChessTournamentService = Depends(get_service)):
    """创建新棋手"""
    try:
        result = service.create_player(**player.dict())
        return PlayerResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/players/{player_id}", response_model=PlayerResponse, tags=["棋手管理"])
async def get_player(player_id: int, service: MockChessTournamentService = Depends(get_service)):
    """根据ID获取棋手信息"""
    player = service.get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail="棋手不存在")
    return PlayerResponse(**player)

@app.get("/players/", response_model=List[PlayerResponse], tags=["棋手管理"])
async def search_players(
    name: Optional[str] = Query(None, description="棋手姓名"),
    rating_min: Optional[int] = Query(None, description="最低等级分"),
    rating_max: Optional[int] = Query(None, description="最高等级分"),
    title: Optional[str] = Query(None, description="称号"),
    service: MockChessTournamentService = Depends(get_service)
):
    """搜索棋手"""
    players = service.search_players(
        name=name, rating_min=rating_min, rating_max=rating_max, title=title
    )
    return [PlayerResponse(**player) for player in players]


# ============= 锦标赛管理API =============

@app.post("/tournaments/", response_model=TournamentResponse, tags=["锦标赛管理"])
async def create_tournament(tournament: TournamentCreate, service: MockChessTournamentService = Depends(get_service)):
    """创建新锦标赛"""
    try:
        result = service.create_tournament(**tournament.dict())
        return TournamentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tournaments/{tournament_code}", response_model=TournamentResponse, tags=["锦标赛管理"])
async def get_tournament(tournament_code: str, service: MockChessTournamentService = Depends(get_service)):
    """根据代码获取锦标赛信息"""
    tournament = service.get_tournament_by_code(tournament_code)
    if not tournament:
        raise HTTPException(status_code=404, detail="锦标赛不存在")
    return TournamentResponse(**tournament)

@app.get("/tournaments/", response_model=List[TournamentResponse], tags=["锦标赛管理"])
async def list_upcoming_tournaments(
    limit: int = Query(10, description="返回数量限制"),
    service: MockChessTournamentService = Depends(get_service)
):
    """获取即将开始的锦标赛列表"""
    tournaments = service.get_upcoming_tournaments(limit)
    return [TournamentResponse(**tournament) for tournament in tournaments]


# ============= 参赛管理API =============

@app.post("/tournaments/registration/", tags=["参赛管理"])
async def register_tournament(registration: TournamentRegistration):
    """注册参加锦标赛"""
    # 实际实现中会调用服务层方法
    return {"message": "注册成功", "tournament_id": registration.tournament_id, "player_id": registration.player_id}

@app.get("/tournaments/{tournament_id}/participants", tags=["参赛管理"])
async def get_tournament_participants(tournament_id: int):
    """获取锦标赛参赛者列表"""
    # 实际实现中会从数据库获取参赛者信息
    return {"tournament_id": tournament_id, "participants": []}


# ============= 比赛管理API =============

@app.post("/matches/", tags=["比赛管理"])
async def create_match(match: MatchCreate):
    """创建比赛"""
    # 实际实现中会调用服务层方法创建比赛
    return {"message": "比赛创建成功", "match": match.dict()}

@app.put("/matches/{match_id}/result", tags=["比赛管理"])
async def update_match_result(match_id: int, result: MatchResultUpdate):
    """更新比赛结果"""
    # 实际实现中会调用服务层方法更新比赛结果
    return {"message": "比赛结果更新成功", "match_id": match_id, "result": result.result}

@app.get("/matches/tournament/{tournament_id}", tags=["比赛管理"])
async def get_tournament_matches(tournament_id: int, round_number: Optional[int] = Query(None)):
    """获取锦标赛的比赛列表"""
    # 实际实现中会从数据库获取比赛信息
    return {"tournament_id": tournament_id, "round_number": round_number, "matches": []}

@app.get("/matches/player/{player_id}", tags=["比赛管理"])
async def get_player_matches(player_id: int, tournament_id: Optional[int] = Query(None)):
    """获取棋手的比赛历史"""
    # 实际实现中会从数据库获取棋手比赛历史
    return {"player_id": player_id, "tournament_id": tournament_id, "matches": []}


# ============= 会员管理API =============

@app.post("/memberships/", tags=["会员管理"])
async def add_member(membership: MembershipCreate):
    """将棋手加入俱乐部"""
    # 实际实现中会调用服务层方法
    return {"message": "会员添加成功", "membership": membership.dict()}

@app.put("/memberships/transfer/{player_id}", tags=["会员管理"])
async def transfer_member(player_id: int, new_club_id: int):
    """转会：将棋手转移到新俱乐部"""
    # 实际实现中会调用服务层方法
    return {"message": "转会成功", "player_id": player_id, "new_club_id": new_club_id}


# ============= 统计查询API =============

@app.get("/statistics/tournament/{tournament_id}", tags=["统计查询"])
async def get_tournament_statistics(tournament_id: int):
    """获取锦标赛统计信息"""
    # 实际实现中会调用服务层方法获取统计数据
    return {
        "tournament_id": tournament_id,
        "participant_count": 50,
        "total_matches": 125,
        "completed_matches": 75,
        "progress_percentage": 60.0,
        "total_rounds": 9,
        "prize_pool": 50000.00,
        "status": "In Progress"
    }

@app.get("/statistics/player/{player_id}", tags=["统计查询"])
async def get_player_statistics(player_id: int, year: Optional[int] = Query(None)):
    """获取棋手统计信息"""
    # 实际实现中会调用服务层方法获取统计数据
    return {
        "player_id": player_id,
        "player_name": "示例棋手",
        "current_rating": 2200,
        "title": "FM",
        "total_games": 45,
        "wins": 25,
        "draws": 15,
        "losses": 5,
        "total_points": 32.5,
        "win_rate": 55.56,
        "tournaments_played": 8
    }

@app.get("/standings/tournament/{tournament_id}", tags=["统计查询"])
async def get_tournament_standings(tournament_id: int):
    """获取锦标赛积分榜"""
    # 实际实现中会从数据库获取积分榜数据
    return {
        "tournament_id": tournament_id,
        "standings": [
            {"rank": 1, "player_name": "张伟", "points": 8.5, "games_played": 9},
            {"rank": 2, "player_name": "李娜", "points": 8.0, "games_played": 9},
            {"rank": 3, "player_name": "王强", "points": 7.5, "games_played": 9}
        ]
    }


# ============= 健康检查 =============

@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/", tags=["系统"])
async def root():
    """根路径，返回API信息"""
    return {
        "message": "国际象棋比赛管理系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# 启动服务器的函数
def start_server():
    """启动FastAPI服务器"""
    uvicorn.run(
        "chess_tournament_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()
