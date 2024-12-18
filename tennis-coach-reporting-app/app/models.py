from flask_login import UserMixin
from app import db
from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Index, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import Enum as PGEnum
import pytz

uk_timezone = pytz.timezone('Europe/London')

class UserRole(Enum):
    COACH = 'coach'
    ADMIN = 'admin'
    SUPER_ADMIN = 'super_admin'

class TennisClub(db.Model):
    __tablename__ = 'tennis_club'
    __table_args__ = (
        Index('idx_tennis_club_subdomain', 'subdomain', unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    # Relationships
    users = db.relationship('User', back_populates='tennis_club', lazy='dynamic')
    groups = db.relationship('TennisGroup', back_populates='tennis_club', lazy='dynamic')
    teaching_periods = db.relationship('TeachingPeriod', back_populates='tennis_club', lazy='dynamic')
    students = db.relationship('Student', back_populates='tennis_club', lazy='dynamic')
    programme_players = db.relationship('ProgrammePlayers', back_populates='tennis_club', lazy='dynamic')

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    __table_args__ = (
        Index('idx_user_email_lower', text('lower(email)'), unique=True),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), nullable=False, unique=True)
    name = db.Column(db.String(100))
    role = db.Column(PGEnum(UserRole, name='userrole'), nullable=False, default=UserRole.COACH)
    is_active = db.Column(db.Boolean, default=True)
    auth_provider = db.Column(db.String(20), default='email')
    auth_provider_id = db.Column(db.String(200))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)

    # Relationships
    tennis_club = db.relationship('TennisClub', back_populates='users')
    reports = db.relationship('Report', back_populates='coach', lazy='dynamic')
    programme_players = db.relationship('ProgrammePlayers', back_populates='coach', lazy='dynamic')

    @property
    def is_admin(self):
        return self.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    @property
    def is_super_admin(self):
        return self.role == UserRole.SUPER_ADMIN

class TennisGroup(db.Model):
    __tablename__ = 'tennis_group'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)

    # Relationships
    tennis_club = db.relationship('TennisClub', back_populates='groups')
    reports = db.relationship('Report', back_populates='tennis_group', lazy='dynamic')
    programme_players = db.relationship('ProgrammePlayers', back_populates='tennis_group', lazy='dynamic')

class TeachingPeriod(db.Model):
    __tablename__ = 'teaching_period'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime(timezone=True), nullable=False)
    end_date = db.Column(db.DateTime(timezone=True), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)

    # Relationships
    tennis_club = db.relationship('TennisClub', back_populates='teaching_periods')
    reports = db.relationship('Report', back_populates='teaching_period', lazy='dynamic')
    programme_players = db.relationship('ProgrammePlayers', back_populates='teaching_period', lazy='dynamic')

class Student(db.Model):
    __tablename__ = 'student'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    contact_email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)

    # Relationships
    tennis_club = db.relationship('TennisClub', back_populates='students')
    reports = db.relationship('Report', back_populates='student', lazy='dynamic')
    programme_players = db.relationship('ProgrammePlayers', back_populates='student', lazy='dynamic')

class ProgrammePlayers(db.Model):
    __tablename__ = 'programme_players'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('tennis_group.id'), nullable=False)
    teaching_period_id = db.Column(db.Integer, db.ForeignKey('teaching_period.id'), nullable=False)
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)
    report_submitted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    # Relationships
    student = db.relationship('Student', back_populates='programme_players')
    coach = db.relationship('User', back_populates='programme_players')
    tennis_group = db.relationship('TennisGroup', back_populates='programme_players')
    teaching_period = db.relationship('TeachingPeriod', back_populates='programme_players')
    tennis_club = db.relationship('TennisClub', back_populates='programme_players')
    reports = db.relationship('Report', back_populates='programme_player', lazy='dynamic')

class Report(db.Model):
    __tablename__ = 'report'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('tennis_group.id'), nullable=False)
    teaching_period_id = db.Column(db.Integer, db.ForeignKey('teaching_period.id'), nullable=False)
    programme_player_id = db.Column(db.Integer, db.ForeignKey('programme_players.id'), nullable=False)
    date = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))

    # Report fields
    forehand = db.Column(db.String(20))
    backhand = db.Column(db.String(20))
    movement = db.Column(db.String(20))
    overall_rating = db.Column(db.Integer)
    next_group_recommendation = db.Column(db.String(50))
    notes = db.Column(db.Text)

    # Relationships
    student = db.relationship('Student', back_populates='reports')
    coach = db.relationship('User', back_populates='reports')
    tennis_group = db.relationship('TennisGroup', back_populates='reports')
    teaching_period = db.relationship('TeachingPeriod', back_populates='reports')
    programme_player = db.relationship('ProgrammePlayers', back_populates='reports')

class CoachQualification(Enum):
    LEVEL_1 = 'Level 1'
    LEVEL_2 = 'Level 2'
    LEVEL_3 = 'Level 3'
    LEVEL_4 = 'Level 4'
    LEVEL_5 = 'Level 5'
    NONE = 'None'

class CoachRole(Enum):
    HEAD_COACH = 'Head Coach'
    SENIOR_COACH = 'Senior Coach'
    LEAD_COACH = 'Lead Coach'
    ASSISTANT_COACH = 'Assistant Coach'
    JUNIOR_COACH = 'Junior Coach'

class CoachDetails(db.Model):
    __tablename__ = 'coach_details'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    tennis_club_id = db.Column(db.Integer, db.ForeignKey('tennis_club.id'), nullable=False)

    # Basic Information
    coach_number = db.Column(db.String(50), unique=True)
    qualification = db.Column(PGEnum(CoachQualification, name='coachqualification'), default=CoachQualification.NONE)
    date_of_birth = db.Column(db.Date)
    contact_number = db.Column(db.String(20))

    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_number = db.Column(db.String(20))

    # Address
    address_line1 = db.Column(db.String(100))
    address_line2 = db.Column(db.String(100))
    city = db.Column(db.String(50))
    postcode = db.Column(db.String(10))

    # Role and UTR
    coach_role = db.Column(PGEnum(CoachRole, name='coachrole'))
    utr_number = db.Column(db.String(20))

    # Accreditations
    accreditation_expiry = db.Column(db.DateTime(timezone=True))
    bcta_accreditation = db.Column(db.String(10), default='N/A')

    # DBS Information
    dbs_number = db.Column(db.String(50))
    dbs_issue_date = db.Column(db.DateTime(timezone=True))
    dbs_expiry = db.Column(db.DateTime(timezone=True))
    dbs_update_service_id = db.Column(db.String(50))

    # First Aid
    pediatric_first_aid = db.Column(db.Boolean, default=False)
    pediatric_first_aid_expiry = db.Column(db.DateTime(timezone=True))
    first_aid_expiry = db.Column(db.DateTime(timezone=True))

    # Safeguarding
    safeguarding_expiry = db.Column(db.DateTime(timezone=True))

    created_at = db.Column(db.DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=text('CURRENT_TIMESTAMP'))

    # Relationships
    user = db.relationship('User', backref=db.backref('coach_details', uselist=False))
    tennis_club = db.relationship('TennisClub', backref='coach_details')

    def get_expiry_status(self, expiry_date):
        if not expiry_date:
            return None

        current_time = datetime.now(uk_timezone)
        if expiry_date.tzinfo != uk_timezone:
            expiry_date = expiry_date.astimezone(uk_timezone)

        days_until_expiry = (expiry_date - current_time).days

        if days_until_expiry < 0:
            return ('expired', days_until_expiry)
        elif days_until_expiry <= 90:
            return ('warning', days_until_expiry)
        else:
            return ('valid', days_until_expiry)
