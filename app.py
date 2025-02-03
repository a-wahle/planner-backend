from flask import Flask, request, jsonify
from models import db, Period,Project,Skill,Component, Contributor, Assignment, ContributorSkill
from config import Config
from datetime import datetime
from flask_cors import CORS
def create_app():
    
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure CORS with expanded settings
    CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",  # Note: removed comma inside string
            "https://planner-web-hebc.vercel.app",
            "https://planner-web-hebc-g92rmo96y-a-wahles-projects.vercel.app"  # Added new domain
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization", 
            "Accept",
            "Origin",
            "Referer",
            "User-Agent",
            "Sec-Fetch-Mode",
            "Sec-Fetch-Site",
            "Sec-Fetch-Dest"
        ]
    }
})
    

    
    # Initialize extensions
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    @app.route('/')
    def index():
        return 'Flask PostgreSQL App'
    
    @app.route('/period', methods=['POST'])
    def create_period():
        data = request.get_json()
        name = data['name']
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
        period = Period(name=name, start_date=start_date, end_date=end_date)
        db.session.add(period)
        db.session.commit()
        return jsonify(period.to_dict()), 201
    
    @app.route('/project', methods=['POST'])
    def create_project():
        data = request.get_json()
        name = data['name']
        description = data['description']
        period_id = data['period_id']
        project = Project(name=name, description=description, period_id=period_id)
        db.session.add(project)
        db.session.flush()

        for component in data.get('components', []):
            project.add_component(component)

        db.session.commit()
        return jsonify(project.to_dict()), 201
    
    @app.route('/skill', methods=['POST'])
    def create_skill():
        data = request.get_json()
        name = data['name']
        skill = Skill(name=name)
        db.session.add(skill)
        db.session.commit()
        return jsonify(skill.to_dict()), 201
    
    @app.route('/component', methods=['POST'])
    def create_component():
        data = request.get_json()
        name = data['name']
        project_id = data['project_id']
        if name == "":
            project_name = db.session.query(Project).get(project_id).name
            skill_name = db.session.query(Skill).get(data['skill_id']).name
            name = project_name + " " + skill_name
        description = data['description']
        
        skill_id = data['skill_id']
        estimated_weeks = data['estimated_weeks']
        component = Component(name=name, description=description, project_id=project_id, skill_id=skill_id, estimated_weeks=estimated_weeks)
        db.session.add(component)
        db.session.commit()
        return jsonify(component.to_dict()), 201
    
    @app.route('/component/<component_id>/estimated_weeks', methods=['PUT'])
    def update_estimated_weeks(component_id):
        data = request.get_json()
        estimated_weeks = data['estimated_weeks']
        component = db.session.query(Component).get(component_id)
        component.estimated_weeks = estimated_weeks
        db.session.commit()
        return jsonify(component.to_dict()), 200

    @app.route('/contributor', methods=['POST'])
    def create_contributor():
        data = request.get_json()
        first_name = data['first_name']
        last_name = data['last_name']
        contributor = Contributor(first_name=first_name, last_name=last_name)
        db.session.add(contributor)
        db.session.flush()
        
        skill_ids = data.get('skill_ids', [])
        for skill_id in skill_ids:
            contributor_skill = ContributorSkill(contributor_id=contributor.contributor_id, skill_id=skill_id)
            db.session.add(contributor_skill)
        db.session.commit()
        return jsonify(contributor.to_dict()), 201
    

    @app.route('/component/<component_id>/assign_contributor', methods=['POST'])
    def assign_contributor(component_id):
        data = request.get_json()
        contributor_id = data['contributor_id']
        component = db.session.query(Component).get(component_id)
        component.assign_contributor(contributor_id)
        db.session.commit()
        return jsonify(component.to_dict()), 200



    @app.route('/assignment', methods=['POST'])
    def create_assignment():
        data = request.get_json()
        component_id = data['component_id']
        contributor_id = data['contributor_id']
        added_weeks = data['added_weeks']
        removed_weeks = data['removed_weeks']
        
        for week in added_weeks:
            assignment = Assignment(component_id=component_id, contributor_id=contributor_id, week=week)
            db.session.add(assignment)
        for week in removed_weeks:
            assignment = db.session.query(Assignment).filter(Assignment.component_id == component_id, Assignment.contributor_id == contributor_id, Assignment.week == week).first()
            db.session.delete(assignment)
        db.session.commit()
        return jsonify(assignment.to_dict()), 201
    
    @app.route('/assignments/contributor/<contributor_id>', methods=['GET'])
    def get_assignments(contributor_id):
        assignments = db.session.query(Assignment).filter(Assignment.contributor_id == contributor_id).order_by(Assignment.week.desc()).all()
        return jsonify([assignment.to_dict() for assignment in assignments]), 200
    
    @app.route('/skills', methods=["GET"])
    def get_skills():
        skills = db.session.query(Skill).all()
        return jsonify([skill.to_dict() for skill in skills]), 200
    
    @app.route('/periods', methods=["GET"])
    def get_periods():
        periods = db.session.query(Period).all()
        return jsonify([period.to_dict() for period in periods]), 200
    
    @app.route('/period/<period_id>/projects', methods=["GET"])
    def get_projects(period_id):
        projects = db.session.query(Project).filter(Project.period_id == period_id).order_by(Project.name).all()

        response = {"projects": [project.to_response() for project in projects]}

        return jsonify(response), 200

    @app.route('/component/<component_id>/assignments', methods=["DELETE"])
    def delete_assignments(component_id):
        component = db.session.query(Component).get(component_id)
        component.clear_assignments()
        db.session.commit()
        return jsonify({"message": "Assignments deleted"}), 200
    
    @app.route('/project/<project_id>', methods=["DELETE"])
    def delete_project(project_id):
        project = db.session.query(Project).get(project_id)
        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": "Project deleted"}), 200

    @app.route('/component/<component_id>', methods=["DELETE"])
    def delete_component(component_id):
        component = db.session.query(Component).get(component_id)
        db.session.delete(component)
        db.session.commit()
        return jsonify({"message": "Component deleted"}), 200
    
    @app.route('/contributors/get_contributors_by_skill/<skill_id>', methods=["GET"])
    def get_contributors_by_skill(skill_id):
        contributors = db.session.query(Contributor).join(ContributorSkill).filter(ContributorSkill.skill_id == skill_id).all()
        return jsonify({"contributors": [contributor.to_dict() for contributor in contributors]}), 200
    
    @app.route('/period/<period_id>/contributor_chart', methods=["GET"])
    def get_contributor_chart(period_id):
        period = db.session.query(Period).get(period_id)
        contributor_chart = period.get_contributor_chart()
        
        return jsonify(contributor_chart), 200
    

    

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
