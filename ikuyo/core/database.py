from sqlmodel import SQLModel, create_engine, Session

# 全局SQLModel engine
engine = create_engine(
    "sqlite:///data/database/ikuyo.db",
    echo=False,
    connect_args={"check_same_thread": False},
)


def get_session():
    """获取SQLModel ORM Session的context manager"""
    return Session(engine)


def create_db_and_tables():
    """初始化所有SQLModel表结构"""
    SQLModel.metadata.create_all(engine)
