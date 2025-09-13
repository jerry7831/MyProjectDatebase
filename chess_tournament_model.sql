-- 国际象棋比赛数据模型 - Oracle数据库设计

-- 1. 俱乐部表 (Clubs)
CREATE TABLE Clubs (
    club_id NUMBER PRIMARY KEY,
    club_name VARCHAR2(100) NOT NULL,
    address CLOB,
    phone VARCHAR2(20),
    email VARCHAR2(100),
    established_date DATE,
    description CLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建序列用于自增主键
CREATE SEQUENCE clubs_seq START WITH 1 INCREMENT BY 1;

-- 创建触发器实现自增
CREATE OR REPLACE TRIGGER clubs_trigger
    BEFORE INSERT ON Clubs
    FOR EACH ROW
BEGIN
    IF :NEW.club_id IS NULL THEN
        :NEW.club_id := clubs_seq.NEXTVAL;
    END IF;
END;
/

-- 2. 棋手表 (Players)
CREATE TABLE Players (
    player_id NUMBER PRIMARY KEY,
    player_name VARCHAR2(100) NOT NULL,
    address CLOB,
    phone VARCHAR2(20),
    email VARCHAR2(100),
    birth_date DATE,
    nationality VARCHAR2(50),
    gender VARCHAR2(10) CHECK (gender IN ('Male', 'Female', 'Other')),
    rating NUMBER DEFAULT 1200, -- 国际象棋等级分
    title VARCHAR2(20), -- 如GM(特级大师), IM(国际大师)等
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建序列和触发器
CREATE SEQUENCE players_seq START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER players_trigger
    BEFORE INSERT ON Players
    FOR EACH ROW
BEGIN
    IF :NEW.player_id IS NULL THEN
        :NEW.player_id := players_seq.NEXTVAL;
    END IF;
END;
/

-- 3. 会员表 (Members) - 棋手与俱乐部的关系
CREATE TABLE Members (
    membership_id NUMBER PRIMARY KEY,
    player_id NUMBER NOT NULL,
    club_id NUMBER NOT NULL,
    join_date DATE NOT NULL,
    membership_type VARCHAR2(20) DEFAULT 'Regular' CHECK (membership_type IN ('Regular', 'Premium', 'Honorary')),
    status VARCHAR2(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Suspended')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_members_player FOREIGN KEY (player_id) REFERENCES Players(player_id) ON DELETE CASCADE,
    CONSTRAINT fk_members_club FOREIGN KEY (club_id) REFERENCES Clubs(club_id) ON DELETE CASCADE,
    
    -- 确保一个棋手在任何时候只能是一个俱乐部的活跃会员
    CONSTRAINT unique_active_membership UNIQUE (player_id, status)
);

-- 创建序列和触发器
CREATE SEQUENCE members_seq START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER members_trigger
    BEFORE INSERT ON Members
    FOR EACH ROW
BEGIN
    IF :NEW.membership_id IS NULL THEN
        :NEW.membership_id := members_seq.NEXTVAL;
    END IF;
END;
/

-- 4. 赞助商表 (Sponsors)
CREATE TABLE Sponsors (
    sponsor_id NUMBER PRIMARY KEY,
    sponsor_name VARCHAR2(100) NOT NULL,
    sponsor_type VARCHAR2(20) NOT NULL CHECK (sponsor_type IN ('Corporate', 'Government', 'Individual', 'Organization')),
    contact_person VARCHAR2(100),
    phone VARCHAR2(20),
    email VARCHAR2(100),
    address CLOB,
    website VARCHAR2(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建序列和触发器
CREATE SEQUENCE sponsors_seq START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER sponsors_trigger
    BEFORE INSERT ON Sponsors
    FOR EACH ROW
BEGIN
    IF :NEW.sponsor_id IS NULL THEN
        :NEW.sponsor_id := sponsors_seq.NEXTVAL;
    END IF;
END;
/

-- 5. 锦标赛表 (Tournaments)
CREATE TABLE Tournaments (
    tournament_id NUMBER PRIMARY KEY,
    tournament_code VARCHAR2(20) UNIQUE NOT NULL,
    tournament_name VARCHAR2(150) NOT NULL,
    hosting_club_id NUMBER,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    location VARCHAR2(200),
    entry_fee NUMBER(10,2) DEFAULT 0.00,
    prize_pool NUMBER(12,2) DEFAULT 0.00,
    max_participants NUMBER DEFAULT 100,
    tournament_type VARCHAR2(20) DEFAULT 'Swiss' CHECK (tournament_type IN ('Swiss', 'Round Robin', 'Knockout', 'Arena')),
    time_control VARCHAR2(50), -- 如 "90+30" (90分钟+30秒)
    status VARCHAR2(20) DEFAULT 'Planned' CHECK (status IN ('Planned', 'Registration Open', 'In Progress', 'Completed', 'Cancelled')),
    description CLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_tournaments_club FOREIGN KEY (hosting_club_id) REFERENCES Clubs(club_id) ON DELETE SET NULL,
    
    -- 确保结束日期不早于开始日期
    CONSTRAINT chk_tournament_dates CHECK (end_date >= start_date)
);

-- 创建序列和触发器
CREATE SEQUENCE tournaments_seq START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER tournaments_trigger
    BEFORE INSERT ON Tournaments
    FOR EACH ROW
BEGIN
    IF :NEW.tournament_id IS NULL THEN
        :NEW.tournament_id := tournaments_seq.NEXTVAL;
    END IF;
END;
/

-- 6. 锦标赛赞助关系表 (Tournament_Sponsors)
CREATE TABLE Tournament_Sponsors (
    tournament_id NUMBER,
    sponsor_id NUMBER,
    sponsorship_amount NUMBER(10,2) DEFAULT 0.00,
    sponsorship_type VARCHAR2(20) DEFAULT 'Supporting' CHECK (sponsorship_type IN ('Title', 'Main', 'Supporting', 'Media')),
    contract_date DATE,
    
    CONSTRAINT pk_tournament_sponsors PRIMARY KEY (tournament_id, sponsor_id),
    CONSTRAINT fk_ts_tournament FOREIGN KEY (tournament_id) REFERENCES Tournaments(tournament_id) ON DELETE CASCADE,
    CONSTRAINT fk_ts_sponsor FOREIGN KEY (sponsor_id) REFERENCES Sponsors(sponsor_id) ON DELETE CASCADE
);

-- 7. 锦标赛参赛者表 (Tournament_Participants)
CREATE TABLE Tournament_Participants (
    tournament_id NUMBER,
    player_id NUMBER,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    seed_number NUMBER, -- 种子排名
    initial_rating NUMBER, -- 参赛时的等级分
    status VARCHAR2(20) DEFAULT 'Registered' CHECK (status IN ('Registered', 'Confirmed', 'Withdrawn', 'Disqualified')),
    
    CONSTRAINT pk_tournament_participants PRIMARY KEY (tournament_id, player_id),
    CONSTRAINT fk_tp_tournament FOREIGN KEY (tournament_id) REFERENCES Tournaments(tournament_id) ON DELETE CASCADE,
    CONSTRAINT fk_tp_player FOREIGN KEY (player_id) REFERENCES Players(player_id) ON DELETE CASCADE
);

-- 8. 比赛表 (Matches)
CREATE TABLE Matches (
    match_id NUMBER PRIMARY KEY,
    tournament_id NUMBER NOT NULL,
    round_number NUMBER NOT NULL,
    board_number NUMBER, -- 台次号
    white_player_id NUMBER NOT NULL,
    black_player_id NUMBER NOT NULL,
    scheduled_time TIMESTAMP,
    actual_start_time TIMESTAMP,
    actual_end_time TIMESTAMP,
    result VARCHAR2(10) DEFAULT '*' CHECK (result IN ('1-0', '0-1', '1/2-1/2', '*')), -- 白胜、黑胜、和棋、未完成
    moves_pgn CLOB, -- PGN格式的棋谱
    time_control_used VARCHAR2(50),
    arbiter VARCHAR2(100), -- 裁判
    status VARCHAR2(20) DEFAULT 'Scheduled' CHECK (status IN ('Scheduled', 'In Progress', 'Completed', 'Postponed', 'Forfeited')),
    notes CLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_matches_tournament FOREIGN KEY (tournament_id) REFERENCES Tournaments(tournament_id) ON DELETE CASCADE,
    CONSTRAINT fk_matches_white_player FOREIGN KEY (white_player_id) REFERENCES Players(player_id) ON DELETE CASCADE,
    CONSTRAINT fk_matches_black_player FOREIGN KEY (black_player_id) REFERENCES Players(player_id) ON DELETE CASCADE,
    
    -- 确保白棋和黑棋不是同一个棋手
    CONSTRAINT chk_different_players CHECK (white_player_id != black_player_id),
    -- 确保结束时间不早于开始时间
    CONSTRAINT chk_match_times CHECK (actual_end_time IS NULL OR actual_start_time IS NULL OR actual_end_time >= actual_start_time)
);

-- 创建序列和触发器
CREATE SEQUENCE matches_seq START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER matches_trigger
    BEFORE INSERT ON Matches
    FOR EACH ROW
BEGIN
    IF :NEW.match_id IS NULL THEN
        :NEW.match_id := matches_seq.NEXTVAL;
    END IF;
END;
/

-- 9. 棋手排名历史表 (Player_Rankings) - 用于追踪等级分变化
CREATE TABLE Player_Rankings (
    ranking_id NUMBER PRIMARY KEY,
    player_id NUMBER NOT NULL,
    rating NUMBER NOT NULL,
    ranking_date DATE NOT NULL,
    tournament_id NUMBER, -- 导致等级分变化的锦标赛
    rating_change NUMBER DEFAULT 0, -- 等级分变化
    games_played NUMBER DEFAULT 0,
    
    CONSTRAINT fk_rankings_player FOREIGN KEY (player_id) REFERENCES Players(player_id) ON DELETE CASCADE,
    CONSTRAINT fk_rankings_tournament FOREIGN KEY (tournament_id) REFERENCES Tournaments(tournament_id) ON DELETE SET NULL,
    
    -- 每个棋手在特定日期只能有一个排名记录
    CONSTRAINT unique_player_date UNIQUE (player_id, ranking_date)
);

-- 创建序列和触发器
CREATE SEQUENCE rankings_seq START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER rankings_trigger
    BEFORE INSERT ON Player_Rankings
    FOR EACH ROW
BEGIN
    IF :NEW.ranking_id IS NULL THEN
        :NEW.ranking_id := rankings_seq.NEXTVAL;
    END IF;
END;
/

-- 10. 锦标赛排行榜表 (Tournament_Standings)
CREATE TABLE Tournament_Standings (
    tournament_id NUMBER,
    player_id NUMBER,
    points NUMBER(3,1) DEFAULT 0.0, -- 积分（胜1分，和0.5分，负0分）
    games_played NUMBER DEFAULT 0,
    wins NUMBER DEFAULT 0,
    draws NUMBER DEFAULT 0,
    losses NUMBER DEFAULT 0,
    buchholz_score NUMBER(5,1) DEFAULT 0.0, -- 布赫霍尔兹分数
    sonneborn_berger NUMBER(5,1) DEFAULT 0.0, -- 索纳博恩-贝格尔分数
    final_rank NUMBER,
    prize_amount NUMBER(10,2) DEFAULT 0.00,
    
    CONSTRAINT pk_tournament_standings PRIMARY KEY (tournament_id, player_id),
    CONSTRAINT fk_standings_tournament FOREIGN KEY (tournament_id) REFERENCES Tournaments(tournament_id) ON DELETE CASCADE,
    CONSTRAINT fk_standings_player FOREIGN KEY (player_id) REFERENCES Players(player_id) ON DELETE CASCADE
);

-- 创建索引以优化查询性能
CREATE INDEX idx_members_player_status ON Members(player_id, status);
CREATE INDEX idx_tournaments_dates ON Tournaments(start_date, end_date);
CREATE INDEX idx_matches_tournament_round ON Matches(tournament_id, round_number);
CREATE INDEX idx_matches_players ON Matches(white_player_id, black_player_id);
CREATE INDEX idx_rankings_player_date ON Player_Rankings(player_id, ranking_date);
CREATE INDEX idx_standings_tournament_points ON Tournament_Standings(tournament_id, points DESC);

-- 创建视图以简化常用查询

-- 视图1: 活跃会员信息
CREATE OR REPLACE VIEW Active_Members AS
SELECT 
    m.membership_id,
    p.player_id,
    p.player_name,
    p.rating,
    p.title,
    c.club_id,
    c.club_name,
    m.join_date,
    m.membership_type
FROM Members m
JOIN Players p ON m.player_id = p.player_id
JOIN Clubs c ON m.club_id = c.club_id
WHERE m.status = 'Active';

-- 视图2: 锦标赛详细信息
CREATE OR REPLACE VIEW Tournament_Details AS
SELECT 
    t.tournament_id,
    t.tournament_code,
    t.tournament_name,
    t.start_date,
    t.end_date,
    c.club_name as hosting_club,
    t.prize_pool,
    t.status,
    COUNT(tp.player_id) as participant_count
FROM Tournaments t
LEFT JOIN Clubs c ON t.hosting_club_id = c.club_id
LEFT JOIN Tournament_Participants tp ON t.tournament_id = tp.tournament_id
WHERE tp.status IN ('Registered', 'Confirmed')
GROUP BY t.tournament_id, t.tournament_code, t.tournament_name, t.start_date, t.end_date, c.club_name, t.prize_pool, t.status;

-- 视图3: 比赛结果汇总
CREATE OR REPLACE VIEW Match_Results AS
SELECT 
    m.match_id,
    t.tournament_name,
    m.round_number,
    m.board_number,
    pw.player_name as white_player,
    pb.player_name as black_player,
    m.result,
    m.scheduled_time,
    m.status
FROM Matches m
JOIN Tournaments t ON m.tournament_id = t.tournament_id
JOIN Players pw ON m.white_player_id = pw.player_id
JOIN Players pb ON m.black_player_id = pb.player_id;

-- 触发器：确保一个棋手在任何时候只能是一个俱乐部的活跃会员
CREATE OR REPLACE TRIGGER ensure_single_active_membership
    BEFORE INSERT ON Members
    FOR EACH ROW
DECLARE
    existing_membership_count NUMBER;
BEGIN
    IF :NEW.status = 'Active' THEN
        SELECT COUNT(*) INTO existing_membership_count
        FROM Members 
        WHERE player_id = :NEW.player_id AND status = 'Active';
        
        IF existing_membership_count > 0 THEN
            RAISE_APPLICATION_ERROR(-20001, 'A player can only have one active membership at a time');
        END IF;
    END IF;
END;
/

-- 触发器：更新棋手等级分
CREATE OR REPLACE TRIGGER update_player_rating
    AFTER UPDATE ON Player_Rankings
    FOR EACH ROW
BEGIN
    IF :NEW.ranking_date >= :OLD.ranking_date THEN
        UPDATE Players 
        SET rating = :NEW.rating 
        WHERE player_id = :NEW.player_id;
    END IF;
END;
/

-- 创建更新时间戳的触发器 (Oracle中没有ON UPDATE CURRENT_TIMESTAMP)
CREATE OR REPLACE TRIGGER clubs_update_timestamp
    BEFORE UPDATE ON Clubs
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER players_update_timestamp
    BEFORE UPDATE ON Players
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER members_update_timestamp
    BEFORE UPDATE ON Members
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER tournaments_update_timestamp
    BEFORE UPDATE ON Tournaments
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

CREATE OR REPLACE TRIGGER matches_update_timestamp
    BEFORE UPDATE ON Matches
    FOR EACH ROW
BEGIN
    :NEW.updated_at := CURRENT_TIMESTAMP;
END;
/

-- 示例数据插入
-- 插入一些示例俱乐部
INSERT INTO Clubs (club_name, address, phone, email, established_date) VALUES
('北京国际象棋俱乐部', '北京市朝阳区某街道123号', '010-12345678', 'beijing@chess.com', DATE '2010-01-15');

INSERT INTO Clubs (club_name, address, phone, email, established_date) VALUES
('上海国际象棋俱乐部', '上海市浦东新区某路456号', '021-87654321', 'shanghai@chess.com', DATE '2008-03-20');

INSERT INTO Clubs (club_name, address, phone, email, established_date) VALUES
('深圳国际象棋俱乐部', '深圳市南山区某大道789号', '0755-11111111', 'shenzhen@chess.com', DATE '2012-06-10');

-- 插入一些示例棋手
INSERT INTO Players (player_name, address, phone, email, birth_date, nationality, gender, rating, title) VALUES
('张伟', '北京市某区某街1号', '13800000001', 'zhangwei@email.com', DATE '1990-05-15', 'Chinese', 'Male', 2200, 'FM');

INSERT INTO Players (player_name, address, phone, email, birth_date, nationality, gender, rating, title) VALUES
('李娜', '上海市某区某路2号', '13800000002', 'lina@email.com', DATE '1992-08-20', 'Chinese', 'Female', 2100, 'WFM');

INSERT INTO Players (player_name, address, phone, email, birth_date, nationality, gender, rating, title) VALUES
('王强', '深圳市某区某街3号', '13800000003', 'wangqiang@email.com', DATE '1988-12-10', 'Chinese', 'Male', 2300, 'IM');

INSERT INTO Players (player_name, address, phone, email, birth_date, nationality, gender, rating, title) VALUES
('刘雪', '广州市某区某路4号', '13800000004', 'liuxue@email.com', DATE '1995-03-25', 'Chinese', 'Female', 1950, NULL);

-- 插入会员关系
INSERT INTO Members (player_id, club_id, join_date, membership_type, status) VALUES
(1, 1, DATE '2023-01-01', 'Premium', 'Active');

INSERT INTO Members (player_id, club_id, join_date, membership_type, status) VALUES
(2, 2, DATE '2023-02-15', 'Regular', 'Active');

INSERT INTO Members (player_id, club_id, join_date, membership_type, status) VALUES
(3, 3, DATE '2023-03-10', 'Premium', 'Active');

INSERT INTO Members (player_id, club_id, join_date, membership_type, status) VALUES
(4, 1, DATE '2023-04-20', 'Regular', 'Active');

-- 插入赞助商
INSERT INTO Sponsors (sponsor_name, sponsor_type, contact_person, phone, email) VALUES
('科技有限公司', 'Corporate', '陈经理', '010-88888888', 'sponsor1@tech.com');

INSERT INTO Sponsors (sponsor_name, sponsor_type, contact_person, phone, email) VALUES
('体育局', 'Government', '李主任', '010-99999999', 'sports@gov.cn');

-- 插入锦标赛
INSERT INTO Tournaments (tournament_code, tournament_name, hosting_club_id, start_date, end_date, location, entry_fee, prize_pool, max_participants, tournament_type, time_control, status) VALUES
('BJOPEN2024', '2024北京公开赛', 1, DATE '2024-06-01', DATE '2024-06-07', '北京市国际会议中心', 200.00, 50000.00, 100, 'Swiss', '90+30', 'Planned');

INSERT INTO Tournaments (tournament_code, tournament_name, hosting_club_id, start_date, end_date, location, entry_fee, prize_pool, max_participants, tournament_type, time_control, status) VALUES
('SHCUP2024', '2024上海杯', 2, DATE '2024-07-15', DATE '2024-07-20', '上海棋院', 150.00, 30000.00, 80, 'Swiss', '120+30', 'Registration Open');

-- 提交事务
COMMIT;

-- 数据模型说明和查询示例将在下一个文件中提供

