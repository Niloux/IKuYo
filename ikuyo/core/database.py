#!/usr/bin/env python3
"""
数据库抽象层 - 读写分离架构
提供统一的数据库连接和查询接口，支持读写分离优化
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from queue import Empty, Full, Queue
from typing import Any, Dict, List, Optional

from .config import load_config


class ReadConnectionPool:
    """只读连接池，支持并发查询"""

    def __init__(self, db_path: str, pool_size: int = 5, timeout: int = 30):
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.connections = Queue(maxsize=pool_size)
        self.active_connections = 0
        self.lock = threading.RLock()

        # 预创建连接
        self._initialize_pool()

    def _initialize_pool(self):
        """初始化连接池"""
        for _ in range(self.pool_size):
            conn = self._create_read_connection()
            if conn:
                self.connections.put(conn)
                self.active_connections += 1

    def _create_read_connection(self) -> Optional[sqlite3.Connection]:
        """创建只读连接"""
        try:
            conn = sqlite3.connect(
                self.db_path, check_same_thread=False, timeout=self.timeout, uri=True
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA query_only = ON")  # 设置为只读
            return conn
        except Exception as e:
            print(f"创建读连接失败: {e}")
            return None

    def _validate_connection(self, conn: sqlite3.Connection) -> bool:
        """验证连接有效性"""
        try:
            conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False

    @contextmanager
    def get_connection(self):
        """获取读连接的上下文管理器"""
        conn = None
        try:
            # 从池中获取连接
            try:
                conn = self.connections.get(timeout=5)
            except Empty:
                # 池中无可用连接，创建临时连接
                conn = self._create_read_connection()
                if not conn:
                    raise Exception("无法创建读连接")

            # 验证连接有效性
            if not self._validate_connection(conn):
                # 连接失效，重新创建
                try:
                    conn.close()
                except:
                    pass
                conn = self._create_read_connection()
                if not conn:
                    raise Exception("无法重建读连接")

            yield conn

        finally:
            if conn:
                try:
                    # 归还连接到池中
                    self.connections.put(conn, timeout=1)
                except Full:
                    # 池满，关闭连接
                    try:
                        conn.close()
                    except:
                        pass

    def get_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        return {
            "pool_size": self.pool_size,
            "available_connections": self.connections.qsize(),
            "active_connections": self.active_connections,
        }

    def close_all(self):
        """关闭所有连接"""
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                conn.close()
            except:
                pass
        self.active_connections = 0


class WriteConnectionManager:
    """单一写连接管理器"""

    def __init__(self, db_path: str, timeout: int = 60):
        self.db_path = db_path
        self.timeout = timeout
        self.write_lock = threading.RLock()
        self._write_conn = None

        # 初始化写连接
        self._initialize_write_connection()

    def _initialize_write_connection(self):
        """初始化写连接"""
        try:
            self._write_conn = sqlite3.connect(
                self.db_path, check_same_thread=False, timeout=self.timeout
            )
            self._write_conn.row_factory = sqlite3.Row

            # 启用WAL模式和性能优化
            self._setup_wal_mode()

        except Exception as e:
            print(f"初始化写连接失败: {e}")
            self._write_conn = None

    def _setup_wal_mode(self):
        """设置WAL模式和性能优化"""
        if not self._write_conn:
            return

        try:
            # 启用WAL模式
            self._write_conn.execute("PRAGMA journal_mode=WAL")

            # 性能优化设置
            self._write_conn.execute("PRAGMA synchronous=NORMAL")
            self._write_conn.execute("PRAGMA cache_size=10000")
            self._write_conn.execute("PRAGMA foreign_keys=ON")

            self._write_conn.commit()
            print("✅ WAL模式已启用，数据库已优化")

        except Exception as e:
            print(f"WAL模式设置失败: {e}")

    def _validate_write_connection(self) -> bool:
        """验证写连接有效性"""
        if not self._write_conn:
            return False
        try:
            self._write_conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False

    def _rebuild_connection(self):
        """重建写连接"""
        if self._write_conn:
            try:
                self._write_conn.close()
            except:
                pass

        self._initialize_write_connection()

    def execute_write(self, query: str, params: tuple = ()) -> int:
        """执行写操作"""
        with self.write_lock:
            # 验证连接有效性
            if not self._validate_write_connection():
                self._rebuild_connection()

            if not self._write_conn:
                raise Exception("写连接不可用")

            try:
                cursor = self._write_conn.execute(query, params)
                self._write_conn.commit()
                return cursor.rowcount
            except Exception as e:
                # 尝试回滚
                try:
                    self._write_conn.rollback()
                except:
                    pass
                raise e

    @contextmanager
    def get_write_connection(self):
        """获取写连接的上下文管理器"""
        with self.write_lock:
            if not self._validate_write_connection():
                self._rebuild_connection()

            if not self._write_conn:
                raise Exception("写连接不可用")

            yield self._write_conn

    def is_healthy(self) -> bool:
        """检查写连接健康状态"""
        return self._validate_write_connection()

    def get_pragma(self, pragma_name: str) -> str:
        """获取PRAGMA设置值"""
        if not self._validate_write_connection():
            return "unknown"

        try:
            if self._write_conn:
                cursor = self._write_conn.execute(f"PRAGMA {pragma_name}")
                result = cursor.fetchone()
                return str(result[0]) if result else "unknown"
            return "unknown"
        except Exception:
            return "unknown"

    def close(self):
        """关闭写连接"""
        with self.write_lock:
            if self._write_conn:
                try:
                    self._write_conn.close()
                except:
                    pass
                self._write_conn = None


class DatabaseManager:
    """数据库连接管理器 - 读写分离架构"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            config = load_config()
            db_path = getattr(config.database, "path", "data/database/ikuyo.db")

        self.db_path = Path(str(db_path))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 加载配置
        self.config = load_config()
        self._load_database_config()

        # 初始化读写分离架构
        self.read_pool = ReadConnectionPool(
            str(self.db_path), self.read_pool_size, self.read_timeout
        )

        self.write_manager = WriteConnectionManager(str(self.db_path), self.write_timeout)

        print(f"✅ 数据库读写分离架构已初始化: {self.db_path}")

    def _load_database_config(self):
        """加载数据库配置"""
        db_config = getattr(self.config, "database", {})

        # 读连接池配置
        read_pool_config = getattr(db_config, "read_pool", {})
        self.read_pool_size = getattr(read_pool_config, "size", 5)
        self.read_timeout = getattr(read_pool_config, "timeout", 30)

        # 写连接配置
        write_config = getattr(db_config, "write_connection", {})
        self.write_timeout = getattr(write_config, "timeout", 60)

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回结果 - 使用读连接池"""
        with self.read_pool.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """执行查询并返回单个结果 - 使用读连接池"""
        with self.read_pool.get_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新操作并返回影响的行数 - 使用写连接"""
        return self.write_manager.execute_write(query, params)

    @contextmanager
    def get_connection(self):
        """向后兼容的连接获取方法"""
        # 分析SQL语句类型，智能路由到读写连接
        # 为了简化，这里返回写连接以保证兼容性
        with self.write_manager.get_write_connection() as conn:
            yield conn

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        return {
            "read_pool": self.read_pool.get_pool_stats(),
            "write_connection": {
                "healthy": self.write_manager.is_healthy(),
                "wal_mode": self.write_manager.get_pragma("journal_mode"),
                "synchronous": self.write_manager.get_pragma("synchronous"),
                "cache_size": self.write_manager.get_pragma("cache_size"),
            },
        }

    def close_all(self):
        """关闭所有连接"""
        self.read_pool.close_all()
        self.write_manager.close()


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
