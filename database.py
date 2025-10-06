from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import config
import json

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    full_name = Column(String(200), nullable=False)
    role = Column(String(50), default='user')
    status = Column(String(100), default='Участник')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    board_link = Column(String(500))
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey('users.id'))

class UserProject(Base):
    __tablename__ = 'user_projects'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    role_in_project = Column(String(100), default='participant')
    joined_at = Column(DateTime, default=datetime.now)

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    image_url = Column(String(500))
    deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(Integer, ForeignKey('users.id'))
    is_active = Column(Boolean, default=True)
    target_users = Column(JSON)  # Список user_id, кому назначено задание

class UserTask(Base):
    __tablename__ = 'user_tasks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False)
    answer_text = Column(Text)
    answer_media = Column(String(500))
    status = Column(String(50), default='pending')
    feedback = Column(Text)
    submitted_at = Column(DateTime, default=datetime.now)
    reviewed_at = Column(DateTime)
    clarification_question = Column(Text)  # Вопрос от пользователя

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    message = Column(Text)
    message_type = Column(String(50), default='info')  # info, feedback, clarification
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class AdminAction(Base):
    __tablename__ = 'admin_actions'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action_type = Column(String(100), nullable=False)
    target_id = Column(Integer)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

# Инициализация базы данных
engine = create_engine(config.DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()