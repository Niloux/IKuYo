#!/usr/bin/env python3
"""
数据库抽象层
提供统一的数据库连接和查询接口，为后续API开发做准备
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import load_config


class DatabaseManager:
    """数据库连接管理器"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            config = load_config()
            db_path = getattr(config.database, "path", "data/database/ikuyo.db")

        self.db_path = Path(str(db_path))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建持久连接（只用于读操作）
        self._read_conn = None
        self._init_read_connection()

    def _init_read_connection(self):
        """初始化只读连接"""
        try:
            self._read_conn = sqlite3.connect(self.db_path)
            self._read_conn.row_factory = sqlite3.Row
            self._read_conn.execute("PRAGMA foreign_keys = ON")
        except Exception:
            self._read_conn = None

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 启用行工厂，支持字典式访问
        conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        # 尝试使用持久连接进行读操作
        if self._read_conn:
            try:
                cursor = self._read_conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
            except Exception:
                # 连接失效，重新创建
                self._init_read_connection()

        # 回退到原有方式
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """执行查询并返回单个结果"""
        # 尝试使用持久连接进行读操作
        if self._read_conn:
            try:
                cursor = self._read_conn.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None
            except Exception:
                # 连接失效，重新创建
                self._init_read_connection()

        # 回退到原有方式
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回影响的行数"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount


class AnimeRepository:
    """动画数据仓库 - 为后续API开发预留的查询接口"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager if db_manager is not None else DatabaseManager()

    def get_anime_by_id(self, mikan_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取动画信息"""
        query = "SELECT * FROM animes WHERE mikan_id = ?"
        return self.db.execute_one(query, (mikan_id,))

    def get_all_animes(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有动画列表"""
        query = "SELECT * FROM animes ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        return self.db.execute_query(query)

    def search_animes_by_title(self, title: str) -> List[Dict[str, Any]]:
        """根据标题搜索动画"""
        query = "SELECT * FROM animes WHERE title LIKE ? ORDER BY created_at DESC"
        return self.db.execute_query(query, (f"%{title}%",))

    def get_anime_resources(self, mikan_id: int) -> List[Dict[str, Any]]:
        """获取动画的所有资源"""
        query = """
        SELECT r.*, sg.name as subtitle_group_name
        FROM resources r
        JOIN subtitle_groups sg ON r.subtitle_group_id = sg.id
        WHERE r.mikan_id = ?
        ORDER BY r.release_date DESC
        """
        return self.db.execute_query(query, (mikan_id,))


class ResourceRepository:
    """资源数据仓库"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager if db_manager is not None else DatabaseManager()

    def get_resources_by_filters(
        self,
        mikan_id: Optional[int] = None,
        resolution: Optional[str] = None,
        episode_number: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """根据条件过滤资源"""
        conditions = []
        params = []

        if mikan_id:
            conditions.append("r.mikan_id = ?")
            params.append(mikan_id)

        if resolution:
            conditions.append("r.resolution = ?")
            params.append(resolution)

        if episode_number:
            conditions.append("r.episode_number = ?")
            params.append(episode_number)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
        SELECT r.*, a.title as anime_title, sg.name as subtitle_group_name
        FROM resources r
        JOIN animes a ON r.mikan_id = a.mikan_id
        JOIN subtitle_groups sg ON r.subtitle_group_id = sg.id
        WHERE {where_clause}
        ORDER BY r.release_date DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        return self.db.execute_query(query, tuple(params))


# 全局数据库管理器实例
db_manager = DatabaseManager()
anime_repo = AnimeRepository(db_manager)
resource_repo = ResourceRepository(db_manager)
