from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID
import uuid
db = SQLAlchemy()

class Period(db.Model):
    __tablename__ = 'periods'
    
    period_id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(80), unique=True, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Align dates to Mondays
        self.start_date = self.start_date - timedelta(days=self.start_date.weekday())
        self.end_date = self.end_date - timedelta(days=self.end_date.weekday())
    
    @property
    def num_weeks(self):
        return (self.end_date - self.start_date).days // 7
    
    def get_contributor_chart(self):
        contributor_chart = {}
        assignment_blobs = (db.session.query(
            Component.name,
            Contributor.contributor_id,
            Contributor.first_name,
            Contributor.last_name,
            Assignment.week
        )
        .join(Project, Component.project_id == Project.project_id)
        .join(Assignment, Component.component_id == Assignment.component_id)
        .join(Contributor, Assignment.contributor_id == Contributor.contributor_id)
        .filter(Project.period_id == self.period_id)
        .order_by(Contributor.first_name, Contributor.last_name)
        .all())

        contributor_chart = {}
        for contributor in db.session.query(Contributor).all():
            contributor_chart[str(contributor.contributor_id)] = {
                "assignments": [[] for _ in range(self.num_weeks)],
                "name": contributor.first_name + " " + contributor.last_name
            }
        for blob in assignment_blobs:
            contributor_chart[str(blob.contributor_id)]["assignments"][blob.week].append(blob.name)

        return contributor_chart
    
    def __repr__(self):
        return f'<Period {self.name}>'
    
    def to_dict(self):
        return {
            'period_id': self.period_id,
            'name': self.name,
            'start_date': self.start_date,
            'end_date': self.end_date
        }

class Project(db.Model):
    __tablename__ = 'projects'
    
    project_id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    period_id = db.Column(UUID, db.ForeignKey('periods.period_id'))
    
    # Relationship
    period = db.relationship('Period', backref=db.backref('projects', lazy=True))

    def add_component(self, component_data):
        skill_id = component_data['skill_id']
        skill = db.session.query(Skill).filter(Skill.skill_id == skill_id).first()

        estimated_weeks = component_data['estimated_weeks']
        component_name = self.name + " " + skill.name

        component = Component(name=component_name, project_id=self.project_id, skill_id=skill_id, estimated_weeks=estimated_weeks)
        db.session.add(component)
    
    def __repr__(self):
        return f'<Project {self.name}>'
    
    def to_dict(self):
        return {
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'period_id': self.period_id,
        }
    
    def to_response(self):
        return {
            'project_id': self.project_id,
            'project_name': self.name,
            'components': sorted([component.to_response() for component in self.components], key=lambda x: x['component_name'])
        }
    
class Skill(db.Model):
    __tablename__ = 'skills'
    
    skill_id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<Skill {self.name}>'
    
    def to_dict(self):
        return {
            'skill_id': self.skill_id,
            'name': self.name
        }

class Component(db.Model):
    __tablename__ = 'components'
    
    component_id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    project_id = db.Column(UUID, db.ForeignKey('projects.project_id', ondelete='CASCADE'))
    skill_id = db.Column(UUID, db.ForeignKey('skills.skill_id'))
    estimated_weeks = db.Column(db.Integer, nullable=True)
    contributor_id = db.Column(UUID, db.ForeignKey('contributors.contributor_id'), nullable=True)
    
    # Relationship
    project = db.relationship('Project', backref=db.backref('components', lazy=True, cascade='all, delete-orphan'))
    skill = db.relationship('Skill', backref=db.backref('components', lazy=True))
    contributor = db.relationship('Contributor', backref=db.backref('components', lazy=True))
    assignments = db.relationship('Assignment', backref=db.backref('component'), 
                                cascade='all, delete-orphan', lazy=True)

    def assert_skill_match(self, contributor_id):
        contributor = Contributor.query.get(contributor_id)
        required_skill_id = self.skill_id
        contributor_skill_ids = [skill.skill_id for skill in contributor.skill_ids]
        return required_skill_id in contributor_skill_ids

    def assign_contributor(self, contributor_id):
        if contributor_id is None:
            self.contributor_id = None
            self.clear_assignments()
            return

        if not self.assert_skill_match(contributor_id):
            raise ValueError("Contributor does not have the required skill")

        if self.contributor_id:
            assignments = self.assignments
            for assignment in assignments:
                assignment.contributor_id = contributor_id
        self.contributor_id = contributor_id
        db.session.commit()

    def clear_assignments(self):
        db.session.query(Assignment).filter(Assignment.component_id == self.component_id).delete()
        db.session.commit()
    
    def __repr__(self):
        return f'<Component {self.name}>'
    
    def to_dict(self):
        return {
            'component_id': self.component_id,
            'name': self.name,
            'description': self.description,
            'project_id': self.project_id,
            'skill_id': self.skill_id
        } 
    
    def to_response(self):

        weeks_in_period = self.project.period.num_weeks

        skill_name = db.session.query(Skill).filter(Skill.skill_id == self.skill_id).first().name
        assignments = db.session.query(Assignment).filter(Assignment.component_id == self.component_id).order_by(Assignment.week).all()
        assignment_chart = [False] * weeks_in_period
        assigned_weeks_count = 0
        for assignment in assignments:
            assignment_chart[assignment.week] = True
            assigned_weeks_count += 1

        response = {
          "component_id": self.component_id,
          "component_name": self.name,
          "estimated_weeks": self.estimated_weeks,
          "assigned_weeks": assigned_weeks_count,
          "skill": skill_name,
          "skill_id": self.skill_id,
          "assignments": assignment_chart,
          "contributor_id": None,
          "contributor_name": None
        }

        if self.contributor:
            response["contributor_name"] = self.contributor.first_name + " " + self.contributor.last_name
            response["contributor_id"] = self.contributor_id

        return response
    
class Contributor(db.Model):
    __tablename__ = 'contributors'
    
    contributor_id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    skill_ids = db.relationship('ContributorSkill', backref='contributors', lazy=True)
    def __repr__(self):
        return f'<Contributor {self.first_name} {self.last_name}>'
    
    def to_dict(self):
        return {
            'contributor_id': self.contributor_id,
            'first_name': self.first_name,
            'last_name': self.last_name
        }
    
class ContributorSkill(db.Model):
    __tablename__ = 'contributor_skills'
    
    contributor_id = db.Column(UUID, db.ForeignKey('contributors.contributor_id'), primary_key=True)
    skill_id = db.Column(UUID, db.ForeignKey('skills.skill_id'), primary_key=True)
    
    def __repr__(self):
        return f'<ContributorSkill {self.contributor_id} {self.skill_id}>'
    
    def to_dict(self):
        return {
            'contributor_id': self.contributor_id,
            'skill_id': self.skill_id
        }
    
class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    component_id = db.Column(UUID, db.ForeignKey('components.component_id', ondelete='CASCADE'), primary_key=True)
    contributor_id = db.Column(UUID, db.ForeignKey('contributors.contributor_id'))
    week = db.Column(db.Integer, primary_key=True)

    # Relationship
    contributor = db.relationship('Contributor', backref=db.backref('assignments', lazy=True))

    def __repr__(self):
        return f'<Assignment {self.component_id} {self.contributor_id}>'
    
    def to_dict(self):
        return {
            'component_id': self.component_id,
            'contributor_id': self.contributor_id,
            'week': self.week
        }


    