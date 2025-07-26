from sqlalchemy import Column, Integer, String, ForeignKey, Enum, JSON, Text, DateTime, Date, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
import datetime

Base = declarative_base()


# Enums для сложности и статусов


class Complexity(PyEnum):
    BASIC = 'basic'
    ADVANCED = 'advanced'
    HIGH = 'high'


class UserStatus(PyEnum):
    NO_SUB = 'no_sub'
    SUB = 'sub'
    TEACHER = 'teacher'


class ReminderType(PyEnum):
    INACTIVE = 'inactive'
    HOLIDAY = 'holiday'
    PROMO = 'promo'


# Модели для задач и теории


class Topic(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)  # Английское название (для кода)
    title_ru = Column(String(100))  # Русское название

    subtopics = relationship("Subtopic", back_populates="topic")
    tasks = relationship("Task", back_populates="topic")
    theories = relationship("Theory", back_populates="topic")


class Subtopic(Base):
    __tablename__ = 'subtopics'
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.id'))
    name = Column(String(50))
    title_ru = Column(String(100))

    topic = relationship("Topic", back_populates="subtopics")
    tasks = relationship("Task", back_populates="subtopic")
    theories = relationship("Theory", back_populates="subtopic")


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    type_number = Column(Integer)  # Номер типа задания в ОГЭ (1-25)
    topic_id = Column(Integer, ForeignKey('topics.id'))
    subtopic_id = Column(Integer, ForeignKey('subtopics.id'), nullable=True)
    complexity = Column(Enum(Complexity))
    task_content = Column(JSON)  # {"text": "...", "image": "url"}
    correct_answer = Column(Text)
    answer_options = Column(JSON)  # ["Вариант 1", "Вариант 2"]
    theory_id = Column(Integer, ForeignKey('theories.id'), nullable=True)
    video_analysis_url = Column(String(255), nullable=True)

    topic = relationship("Topic", back_populates="tasks")
    subtopic = relationship("Subtopic", back_populates="tasks")
    theory = relationship("Theory", back_populates="tasks")


class Theory(Base):
    __tablename__ = 'theories'
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.id'))
    subtopic_id = Column(Integer, ForeignKey('subtopics.id'), nullable=True)
    complexity = Column(Enum(Complexity))
    content = Column(Text)  # Markdown?
    examples = Column(JSON)  # [{"task": "...", "solution": "..."}]

    topic = relationship("Topic", back_populates="theories")
    subtopic = relationship("Subtopic", back_populates="theories")
    tasks = relationship("Task", back_populates="theory")


# Модели пользователей


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(Enum(UserStatus), default=UserStatus.NO_SUB)
    phone = Column(String(20), nullable=True)
    city = Column(String(50), nullable=True)
    last_interaction_time = Column(DateTime)

    stats = relationship("UserStat", back_populates="user")
    progress = relationship(
        "UserProgress", back_populates="user", uselist=False)
    achievements = relationship("UserAchievement", back_populates="user")


class UserStat(Base):
    __tablename__ = 'user_stats'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), primary_key=True)
    subtopic_id = Column(Integer, ForeignKey('subtopics.id'), primary_key=True)
    correct_answers = Column(Integer, default=0)
    total_attempts = Column(Integer, default=0)
    percentage = Column(Float, default=0.0)

    user = relationship("User", back_populates="stats")
    topic = relationship("Topic")
    subtopic = relationship("Subtopic")


class UserProgress(Base):
    __tablename__ = 'user_progress'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    daily_record = Column(Integer, default=0)
    weekly_points = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    last_active_day = Column(Date)

    user = relationship("User", back_populates="progress")


class UserAchievement(Base):
    __tablename__ = 'user_achievements'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    achievement_id = Column(Integer, ForeignKey(
        'achievements.id'), primary_key=True)
    unlocked_at = Column(DateTime, nullable=True)
    progress = Column(Integer, default=0)

    user = relationship("User", back_populates="achievements")
    achievement = relationship(
        "Achievement", back_populates="user_achievements")


# Достижения и напоминания


class Achievement(Base):
    __tablename__ = 'achievements'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(Text)
    reward_points = Column(Integer)
    condition = Column(Text)  # Логика проверки

    user_achievements = relationship(
        "UserAchievement", back_populates="achievement")


class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    reminder_type = Column(Enum(ReminderType))
    text = Column(Text)
