from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DB_URL = "postgresql://micro_admin:micro_pass@perf_db_container:5432/perf_db"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class Training_metrics(Base):
    __tablename__ = "training_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    library = Column(String)
    dataset = Column(String)
    epoch = Column(Integer)
    
    accuracy = Column(Float)
    duree = Column(Integer)
    ram_usage = Column(Integer)
    cpu_usage = Column(Integer)

class Result_metrics(Base):
    __tablename__ = "result_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    library = Column(String)
    dataset = Column(String)
    
    accuracy = Column(Float)

Base.metadata.create_all(engine)