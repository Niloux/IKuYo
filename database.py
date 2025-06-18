import sqlite3
from contextlib import contextmanager

DB_PATH = 'mikan.db'

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        c = conn.cursor()
        # 动画基础信息表
        c.execute('''
        CREATE TABLE IF NOT EXISTS animes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mikan_id INTEGER UNIQUE,
            bangumi_id INTEGER UNIQUE,
            title TEXT NOT NULL,
            original_title TEXT,
            broadcast_day TEXT,
            broadcast_start TEXT,
            official_website TEXT,
            bangumi_url TEXT,
            description TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT
        )''')
        # 字幕组信息表
        c.execute('''
        CREATE TABLE IF NOT EXISTS subtitle_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            last_update TEXT,
            is_subscribed INTEGER DEFAULT 0,
            created_at TEXT
        )''')
        # 动画-字幕组关联表
        c.execute('''
        CREATE TABLE IF NOT EXISTS anime_subtitle_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER,
            subtitle_group_id INTEGER,
            last_update TEXT,
            FOREIGN KEY (anime_id) REFERENCES animes(id),
            FOREIGN KEY (subtitle_group_id) REFERENCES subtitle_groups(id)
        )''')
        # 资源文件表
        c.execute('''
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anime_id INTEGER,
            subtitle_group_id INTEGER,
            episode_number INTEGER,
            title TEXT NOT NULL,
            file_size TEXT,
            resolution TEXT,
            subtitle_type TEXT,
            download_url TEXT,
            magnet_hash TEXT,
            release_date TEXT,
            created_at TEXT,
            FOREIGN KEY (anime_id) REFERENCES animes(id),
            FOREIGN KEY (subtitle_group_id) REFERENCES subtitle_groups(id)
        )''')
        # 爬取日志表
        c.execute('''
        CREATE TABLE IF NOT EXISTS crawl_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spider_name TEXT,
            anime_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            items_count INTEGER,
            status TEXT,
            error_message TEXT,
            FOREIGN KEY (anime_id) REFERENCES animes(id)
        )''')
        conn.commit()
