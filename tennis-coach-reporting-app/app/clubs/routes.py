from flask import Blueprint, request, render_template, flash, redirect, url_for, session, make_response, current_app
from app import db
from app.models import TennisClub, User, TennisGroup, TeachingPeriod, UserRole, Student, ProgrammePlayers, CoachDetails, CoachQualification, CoachRole
from datetime import datetime, timedelta
from flask_login import login_required, current_user, login_user
import traceback
import pandas as pd 
from werkzeug.utils import secure_filename 
from datetime import datetime 
from app.utils.auth import admin_required
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import pytz
import json

# Get UK timezone
uk_timezone = pytz.timezone('Europe/London')

club_management = Blueprint('club_management', __name__, url_prefix='/clubs') 

ALLOWED_EXTENSIONS = {'csv'}  # Since we only want CSV files to upload players

# Add this helper function
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@club_management.context_processor
def utility_processor():
   from app.models import UserRole
   return {'UserRole': UserRole}

def setup_default_groups(club_id):
   groups = [
       {"name": "Beginners", "description": "New players learning basics"},
       {"name": "Intermediate", "description": "Players developing core skills"},
       {"name": "Advanced", "description": "Competitive players"}
   ]
   for group in groups:
       db.session.add(TennisGroup(tennis_club_id=club_id, **group))

def setup_initial_teaching_period(club_id):
   start_date = datetime.now()
   db.session.add(TeachingPeriod(
       tennis_club_id=club_id,
       name=f"Teaching Period {start_date.strftime('%B %Y')}",
       start_date=start_date, 
       end_date=start_date + timedelta(weeks=12)
   ))

@club_management.route('/onboard', methods=['GET', 'POST'])
def onboard_club():
   if request.method == 'GET':
       return render_template('admin/club_onboarding.html')

   try:
       club = TennisClub(
           name=request.form['club_name'],
           subdomain=request.form['subdomain']
       )
       db.session.add(club)
       db.session.flush()

       admin = User(
           email=request.form['admin_email'],
           username=f"admin_{request.form['subdomain']}",
           name=request.form['admin_name'],
           role=UserRole.ADMIN,
           tennis_club_id=club.id,
           is_active=True
       )
       db.session.add(admin)
       
       setup_default_groups(club.id)
       setup_initial_teaching_period(club.id)
       
       db.session.commit()
       flash('Tennis club created successfully', 'success')
       return redirect(url_for('main.home'))
       
   except Exception as e:
       db.session.rollback()
       flash(f'Error creating club: {str(e)}', 'error')
       return redirect(url_for('club_management.onboard_club'))

@club_management.route('/manage/<int:club_id>', methods=['GET', 'POST'])
@login_required
def manage_club(club_id):
   print(f"Managing club {club_id} for user {current_user.id} with role {current_user.role}")
   
   club = TennisClub.query.get_or_404(club_id)
   
   if not current_user.is_admin and not current_user.is_super_admin:
       print(f"Access denied: User {current_user.id} is not an admin")
       flash('You must be an admin to manage club settings', 'error')
       return redirect(url_for('main.home'))
       
   if current_user.tennis_club_id != club.id:
       print(f"Access denied: User's club {current_user.tennis_club_id} doesn't match requested club {club.id}")
       flash('You can only manage your own tennis club', 'error')
       return redirect(url_for('main.home'))
   
   if request.method == 'POST':
       club.name = request.form['name']
       club.subdomain = request.form['subdomain']
       
       try:
           db.session.commit()
           flash('Club details updated successfully', 'success')
           return redirect(url_for('main.home'))
       except Exception as e:
           db.session.rollback()
           flash(f'Error updating club: {str(e)}', 'error')
           
   return render_template('admin/manage_club.html', club=club)

@club_management.route('/manage/<int:club_id>/teaching-periods', methods=['GET', 'POST'])
@login_required
def manage_teaching_periods(club_id):
    print(f"Managing teaching periods for club {club_id}")
    
    club = TennisClub.query.get_or_404(club_id)
    
    if not current_user.is_admin and not current_user.is_super_admin:
        flash('You must be an admin to manage teaching periods', 'error')
        return redirect(url_for('main.home'))
        
    if current_user.tennis_club_id != club.id:
        flash('You can only manage teaching periods for your own tennis club', 'error')
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        try:
            if action == 'add_period':
                # Handle adding new period
                name = request.form['name']
                start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
                end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
                
                if start_date > end_date:
                    flash('Start date must be before end date', 'error')
                else:
                    period = TeachingPeriod(
                        name=name,
                        start_date=start_date,
                        end_date=end_date,
                        tennis_club_id=club.id
                    )
                    db.session.add(period)
                    db.session.commit()
                    flash('Teaching period created successfully', 'success')

            elif action == 'edit_period':
                # Handle editing period
                period_id = request.form.get('period_id')
                period = TeachingPeriod.query.get_or_404(period_id)
                
                period.name = request.form['name']
                period.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
                period.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
                
                if period.start_date > period.end_date:
                    flash('Start date must be before end date', 'error')
                else:
                    db.session.commit()
                    flash('Teaching period updated successfully', 'success')

            elif action == 'delete_period':
                # Handle deleting period
                period_id = request.form.get('period_id')
                period = TeachingPeriod.query.get_or_404(period_id)
                
                if period.reports.count() > 0:  # Changed from if period.reports:
                    flash('Cannot delete teaching period with existing reports', 'error')
                else:
                    db.session.delete(period)
                    db.session.commit()
                    flash('Teaching period deleted successfully', 'success')
                    
        except Exception as e:
            db.session.rollback()
            print(f"Error managing teaching period: {str(e)}")
            print(traceback.format_exc())
            flash(f'Error managing teaching period: {str(e)}', 'error')

        return redirect(url_for('club_management.manage_teaching_periods', club_id=club.id))
    
    teaching_periods = TeachingPeriod.query.filter_by(
        tennis_club_id=club.id
    ).order_by(TeachingPeriod.start_date.desc()).all()
    
    return render_template('admin/manage_teaching_periods.html', 
                         club=club, 
                         teaching_periods=teaching_periods)

@club_management.route('/onboard-coach', methods=['GET', 'POST'])
def onboard_coach():
    temp_user_info = session.get('temp_user_info')
   
    if request.method == 'POST':
        club_id = request.form.get('club_id')
       
        if not club_id:
            flash('Please select a tennis club', 'error')
            return redirect(url_for('club_management.onboard_coach'))
           
        club = TennisClub.query.get(club_id)
       
        if not club:
            flash('Invalid tennis club selected', 'error')
            return redirect(url_for('club_management.onboard_coach'))
       
        try:
            if temp_user_info:
                user = User.query.filter_by(email=temp_user_info['email']).first()
                if not user:
                    # Generate a unique username
                    base_username = f"coach_{temp_user_info['email'].split('@')[0]}"
                    username = base_username
                    counter = 1
                    
                    # Keep checking until we find a unique username
                    while User.query.filter_by(username=username).first():
                        username = f"{base_username}_{counter}"
                        counter += 1
                    
                    user = User(
                        email=temp_user_info['email'],
                        username=username,  # Use the unique username
                        name=temp_user_info['name'],
                        role=UserRole.COACH,
                        auth_provider='google',
                        auth_provider_id=temp_user_info['provider_id'],
                        is_active=True,
                        tennis_club_id=club.id
                    )
                    db.session.add(user)
                else:
                    user.tennis_club_id = club.id
                    user.auth_provider = 'google'
                    user.auth_provider_id = temp_user_info['provider_id']
               
                db.session.commit()
                login_user(user)
                session.pop('temp_user_info', None)
               
                flash('Welcome to your tennis club!', 'success')
                return redirect(url_for('main.home'))
            else:
                flash('User information not found. Please try logging in again.', 'error')
                return redirect(url_for('main.login'))
               
        except Exception as e:
            db.session.rollback()
            print(f"Error in onboarding: {str(e)}")
            flash('An error occurred during onboarding', 'error')
            return redirect(url_for('club_management.onboard_coach'))
   
    clubs = TennisClub.query.all()
    return render_template('admin/coach_onboarding.html', clubs=clubs)

def parse_date(date_str):
    """Parse date from DD-MMM-YYYY format (e.g., 05-Nov-2013)"""
    print(f"Attempting to parse date: '{date_str}'")
    print(date_str)
    if not date_str or not isinstance(date_str, str):
        raise ValueError(f"Invalid date input: {date_str}")

    try:
        # Clean up the date string and split
        date_str = date_str.strip()
        day, month, year = date_str.split('-')
        
        # Ensure month is properly capitalized
        month = month.capitalize()
        
        # Reconstruct date string in proper format
        formatted_date_str = f"{day}-{month}-{year}"
        
        # Parse using strptime
        parsed_date = datetime.strptime(formatted_date_str, '%d-%b-%Y').date()
        print(f"Successfully parsed date: {parsed_date}")
        return parsed_date
        
    except ValueError as e:
        print(f"Date parsing failed: {str(e)}")
        raise ValueError(f"Invalid date format for '{date_str}'. Use DD-MMM-YYYY format (e.g., 05-Nov-2013)")

def bulk_upload_players(club, teaching_period_id, file):
    try:
        # Read CSV file
        df = pd.read_csv(file)
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        # Verify required columns
        required_columns = ['student_name', 'date_of_birth', 'contact_email', 'coach_email', 'group_name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f'Missing columns: {", ".join(missing_columns)}')
        
        # Get all coaches and groups for the club
        coaches = {coach.email.lower(): coach for coach in 
                 User.query.filter_by(tennis_club_id=club.id).all()}
        groups = {group.name.lower(): group for group in 
                 TennisGroup.query.filter_by(tennis_club_id=club.id).all()}
        
        # Verify teaching period
        teaching_period = TeachingPeriod.query.get(teaching_period_id)
        if not teaching_period or teaching_period.tennis_club_id != club.id:
            raise ValueError('Invalid teaching period selected')
        
        students_created = 0
        players_created = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                print("going into parse_date")
                print(row['date_of_birth'])
                # Parse date of birth
                date_of_birth = parse_date(row['date_of_birth'])
                print(date_of_birth)

                # Create or update student
                student = Student.query.filter_by(
                    name=row['student_name'].strip(),
                    tennis_club_id=club.id
                ).first()

                if not student:
                    student = Student(
                        name=row['student_name'].strip(),
                        date_of_birth=date_of_birth,
                        contact_email=row['contact_email'].strip(),
                        tennis_club_id=club.id
                    )
                    db.session.add(student)
                    students_created += 1
                else:
                    student.date_of_birth = date_of_birth
                    student.contact_email = row['contact_email'].strip()
                
                db.session.flush()
                
                # Verify coach exists
                coach_email = row['coach_email'].lower()
                if coach_email not in coaches:
                    raise ValueError(f"Coach email '{row['coach_email']}' not found")

                # Verify group exists
                group_name = row['group_name'].lower()
                if group_name not in groups:
                    raise ValueError(f"Group '{row['group_name']}' not found")
                
                # Check for existing assignment
                existing_assignment = ProgrammePlayers.query.filter_by(
                    student_id=student.id,
                    teaching_period_id=teaching_period_id,
                    tennis_club_id=club.id
                ).first()
                
                if existing_assignment:
                    existing_assignment.coach_id = coaches[coach_email].id
                    existing_assignment.group_id = groups[group_name].id
                else:
                    assignment = ProgrammePlayers(
                        student_id=student.id,
                        coach_id=coaches[coach_email].id,
                        group_id=groups[group_name].id,
                        teaching_period_id=teaching_period_id,
                        tennis_club_id=club.id
                    )
                    db.session.add(assignment)
                    players_created += 1

            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                continue
        
        if errors:
            db.session.rollback()
            return students_created, players_created, errors
        else:
            db.session.commit()
            return students_created, players_created, None
        
    except Exception as e:
        db.session.rollback()
        raise e

@club_management.route('/manage/<int:club_id>/players', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_players(club_id):
    club = TennisClub.query.get_or_404(club_id)
    
    # Get all teaching periods
    periods = TeachingPeriod.query.filter_by(
        tennis_club_id=club.id
    ).order_by(TeachingPeriod.start_date.desc()).all()
    
    # Get selected period (default to most recent if none selected)
    selected_period_id = request.args.get('period', type=int)
    if not selected_period_id and periods:
        selected_period_id = periods[0].id
    
    # Handle CSV upload
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                students_created, players_created, errors = bulk_upload_players(
                    club, selected_period_id, file
                )
                
                if errors:
                    for error in errors:
                        flash(error, 'error')
                else:
                    flash(f'Successfully added {students_created} new students and {players_created} players', 'success')
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                
        return redirect(request.url)
    
    # Get players for selected period
    players = []
    if selected_period_id:
        players = ProgrammePlayers.query.filter_by(
            tennis_club_id=club.id,
            teaching_period_id=selected_period_id
        ).order_by(ProgrammePlayers.created_at.desc()).all()
    
    available_groups = TennisGroup.query.filter_by(tennis_club_id=club.id).all()
    
    return render_template(
        'admin/programme_players.html',
        club=club,
        periods=periods,
        selected_period_id=selected_period_id,
        players=players,
        available_groups=available_groups
    )

@club_management.route('/manage/<int:club_id>/players/download-template')
@login_required
@admin_required
def download_assignment_template(club_id):
    """Download a CSV template for player assignments"""
    club = TennisClub.query.get_or_404(club_id)
    
    # Create CSV content with headers and example rows
    csv_content = [
        "student_name,date_of_birth,contact_email,coach_email,group_name",
        "John Smith,05-Nov-2013,parent@example.com,coach@example.com,Red 1",
        "Emma Jones,22-Mar-2014,emma.parent@example.com,coach@example.com,Red 2"
    ]
    
    # Add comment explaining the format
    csv_content.insert(0, "# Date format must be DD-MMM-YYYY (e.g., 05-Nov-2013, 22-Mar-2014)")
    csv_content.insert(1, "#")
    
    csv_data = "\n".join(csv_content)
    
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=programme_players_template_{club.name.lower().replace(" ", "_")}.csv'
    
    return response

@club_management.route('/manage/<int:club_id>/players/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_player(club_id):
    club = TennisClub.query.get_or_404(club_id)

    if not (current_user.is_admin or current_user.is_super_admin):
        current_app.logger.error(f"User {current_user.id} is not an admin, access denied")
        flash('You must be an admin to add players', 'error')
        return redirect(url_for('main.dashboard'))

    if current_user.tennis_club_id != club.id:
        current_app.logger.error(f"User {current_user.id} tried to add player to club {club.id} which is not their own")
        flash('You can only add players to your own tennis club', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        try:
            # Get form data
            student_name = request.form['student_name'].strip()
            contact_email = request.form['contact_email'].strip()
            coach_id = request.form['coach_id']
            group_id = request.form['group_id']
            teaching_period_id = request.form['teaching_period_id']

            # Handle date of birth - the form will send in YYYY-MM-DD format
            try:
                dob_str = request.form['date_of_birth']
                date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please select a valid date.', 'error')
                return redirect(request.url)

            current_app.logger.info(f"Attempting to add player: student_name={student_name}, date_of_birth={date_of_birth}, contact_email={contact_email}, coach_id={coach_id}, group_id={group_id}, teaching_period_id={teaching_period_id}")

            # Verify the coach belongs to this club
            coach = User.query.filter_by(id=coach_id, tennis_club_id=club.id).first()
            if not coach:
                current_app.logger.error(f"Selected coach with ID {coach_id} is not part of the club")
                flash('Selected coach is not part of your tennis club', 'error')
                return redirect(request.url)

            # Create or get student
            student = Student.query.filter_by(
                name=student_name,
                tennis_club_id=club.id
            ).first()

            if not student:
                student = Student(
                    name=student_name,
                    date_of_birth=date_of_birth,
                    contact_email=contact_email,
                    tennis_club_id=club.id
                )
                db.session.add(student)
                db.session.flush()

            # Check for existing assignment
            existing_assignment = ProgrammePlayers.query.filter_by(
                student_id=student.id,
                teaching_period_id=teaching_period_id,
                tennis_club_id=club.id
            ).first()

            if existing_assignment:
                flash('Student is already assigned to this teaching period', 'error')
                return redirect(request.url)

            # Create programme player assignment
            assignment = ProgrammePlayers(
                student_id=student.id,
                coach_id=coach_id,
                group_id=group_id,
                teaching_period_id=teaching_period_id,
                tennis_club_id=club.id
            )

            db.session.add(assignment)
            db.session.commit()

            current_app.logger.info(f"Player added successfully: student_id={student.id}, coach_id={coach_id}, group_id={group_id}, teaching_period_id={teaching_period_id}")
            flash('Player added successfully', 'success')
            return redirect(url_for('club_management.manage_players', club_id=club.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding player: {str(e)}")
            flash(f'Error adding player: {str(e)}', 'error')
            return redirect(request.url)

    # Get all users and groups for the form
    club_users = User.query.filter_by(tennis_club_id=club.id).all()
    groups = TennisGroup.query.filter_by(tennis_club_id=club.id).all()
    periods = TeachingPeriod.query.filter_by(tennis_club_id=club.id).order_by(TeachingPeriod.start_date.desc()).all()

    return render_template('admin/add_programme_player.html',
                         club=club,
                         club_users=club_users,
                         groups=groups,
                         periods=periods)

@club_management.route('/manage/<int:club_id>/players/<int:player_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_player(club_id, player_id):
    club = TennisClub.query.get_or_404(club_id)
    player = ProgrammePlayers.query.get_or_404(player_id)
    
    if not (current_user.is_admin or current_user.is_super_admin):
        flash('You must be an admin to edit players', 'error')
        return redirect(url_for('main.dashboard'))
        
    if current_user.tennis_club_id != club.id:
        flash('You can only edit players in your own tennis club', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        try:
            # Update student info
            player.student.name = request.form['student_name'].strip()
            player.student.contact_email = request.form['contact_email'].strip()
            
            # Handle date of birth update
            try:
                dob_str = request.form['date_of_birth']
                if dob_str:  # Only update if a date was provided
                    date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    player.student.date_of_birth = date_of_birth
            except ValueError:
                flash('Invalid date format. Please select a valid date.', 'error')
                return redirect(request.url)
            
            # Verify the coach belongs to this club
            coach_id = request.form['coach_id']
            coach = User.query.filter_by(id=coach_id, tennis_club_id=club.id).first()
            if not coach:
                flash('Selected coach is not part of your tennis club', 'error')
                return redirect(request.url)
            
            # Update assignment
            player.coach_id = coach_id
            player.group_id = request.form['group_id']
            
            db.session.commit()
            flash('Player updated successfully', 'success')
            return redirect(url_for('club_management.manage_players', club_id=club.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating player: {str(e)}', 'error')
            return redirect(request.url)

    # Get all users and groups for the form
    club_users = User.query.filter_by(
        tennis_club_id=club.id
    ).order_by(User.name).all()
    
    groups = TennisGroup.query.filter_by(
        tennis_club_id=club.id
    ).order_by(TennisGroup.name).all()

    return render_template('admin/edit_programme_player.html',
                         club=club,
                         player=player,
                         club_users=club_users,
                         groups=groups)

@club_management.route('/manage/<int:club_id>/players/<int:player_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_player(club_id, player_id):
    club = TennisClub.query.get_or_404(club_id)
    player = ProgrammePlayers.query.get_or_404(player_id)
    
    if not (current_user.is_admin or current_user.is_super_admin):
        flash('You must be an admin to delete players', 'error')
        return redirect(url_for('main.dashboard'))
        
    if current_user.tennis_club_id != club.id:
        flash('You can only delete players in your own tennis club', 'error')
        return redirect(url_for('main.dashboard'))

    try:
        # Only remove from programme, don't delete student record
        db.session.delete(player)
        db.session.commit()
        flash('Player successfully removed from the programme', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error removing player: {str(e)}', 'error')

    return redirect(url_for('club_management.manage_players', club_id=club.id))

@club_management.route('/manage/<int:club_id>/groups', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_groups(club_id):
    try:
        club = TennisClub.query.get_or_404(club_id)

        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add_group':
                group_name = request.form.get('group_name', '').strip()
                group_description = request.form.get('group_description', '').strip()
                
                if not group_name:
                    flash('Group name is required', 'error')
                    return redirect(url_for('club_management.manage_groups', club_id=club_id))

                existing_group = TennisGroup.query.filter_by(
                    tennis_club_id=club.id, 
                    name=group_name
                ).first()
                
                if existing_group:
                    flash('A group with this name already exists', 'error')
                else:
                    try:
                        new_group = TennisGroup(
                            name=group_name,
                            description=group_description,
                            tennis_club_id=club.id
                        )
                        db.session.add(new_group)
                        db.session.commit()
                        flash('New group added successfully', 'success')
                    except SQLAlchemyError as e:
                        db.session.rollback()
                        flash(f'Error adding group: {str(e)}', 'error')
                    
            elif action == 'edit_group':
                group_id = request.form.get('group_id')
                group_name = request.form.get('group_name', '').strip()
                group_description = request.form.get('group_description', '').strip()

                if not group_name:
                    flash('Group name is required', 'error')
                    return redirect(url_for('club_management.manage_groups', club_id=club_id))

                group = TennisGroup.query.get_or_404(group_id)
                
                # Check if the group belongs to this club
                if group.tennis_club_id != club.id:
                    flash('You do not have permission to edit this group', 'error')
                    return redirect(url_for('club_management.manage_groups', club_id=club_id))

                # Check if name already exists for another group
                existing_group = TennisGroup.query.filter(
                    TennisGroup.tennis_club_id == club.id,
                    TennisGroup.name == group_name,
                    TennisGroup.id != group_id
                ).first()

                if existing_group:
                    flash('A group with this name already exists', 'error')
                else:
                    try:
                        group.name = group_name
                        group.description = group_description
                        db.session.commit()
                        flash('Group updated successfully', 'success')
                    except SQLAlchemyError as e:
                        db.session.rollback()
                        flash(f'Error updating group: {str(e)}', 'error')

            elif action == 'delete_group':
                group_id = request.form.get('group_id')
                group = TennisGroup.query.get_or_404(group_id)

                # Check if the group belongs to this club
                if group.tennis_club_id != club.id:
                    flash('You do not have permission to delete this group', 'error')
                    return redirect(url_for('club_management.manage_groups', club_id=club_id))

                # Check if the group has any players assigned to it
                if group.programme_players:
                    flash('Cannot delete group with players assigned to it', 'error')
                else:
                    try:
                        db.session.delete(group)
                        db.session.commit()
                        flash('Group deleted successfully', 'success')
                    except SQLAlchemyError as e:
                        db.session.rollback()
                        flash(f'Error deleting group: {str(e)}', 'error')
            
            else:
                flash('Invalid action', 'error')

        # Get all groups for this club
        groups = TennisGroup.query.filter_by(tennis_club_id=club.id).order_by(TennisGroup.name).all()
        return render_template('admin/manage_groups.html', club=club, groups=groups)

    except SQLAlchemyError as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('main.home'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('main.home'))

def parse_birth_date(date_str):
    """Parse birth date string to date object."""
    if date_str:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None
    return None

def days_until_expiry(expiry_date):
        """Calculate days until expiry for a given date."""
        if expiry_date is None:
            return None, None
            
        # Convert expiry date to UK timezone if it isn't already
        if hasattr(expiry_date, 'tzinfo') and expiry_date.tzinfo != uk_timezone:
            expiry_date = expiry_date.astimezone(uk_timezone)
        
        current_time = datetime.now(uk_timezone)
        
        # Set both dates to midnight for accurate day calculation
        if hasattr(expiry_date, 'replace'):
            expiry_midnight = expiry_date.replace(hour=0, minute=0, second=0, microsecond=0)
            current_midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            # Handle date objects
            expiry_midnight = datetime.combine(expiry_date, datetime.min.time())
            current_midnight = datetime.combine(current_time.date(), datetime.min.time())
            expiry_midnight = uk_timezone.localize(expiry_midnight)
            current_midnight = uk_timezone.localize(current_midnight)
        
        days = (expiry_midnight - current_midnight).days
        
        if days < 0:
            return 'expired', days
        elif days <= 90:
            return 'warning', days
        else:
            return 'valid', days

@club_management.route('/manage/<int:club_id>/coaches', methods=['GET'])
@login_required
@admin_required
def manage_coaches(club_id):
    club = TennisClub.query.get_or_404(club_id)
    
    if current_user.tennis_club_id != club.id:
        flash('You can only manage coaches in your own tennis club', 'error')
        return redirect(url_for('main.dashboard'))

    # Get all coaches for this club
    coaches = User.query.filter_by(
        tennis_club_id=club.id
    ).order_by(User.name).all()
    
    # Get coach details for all coaches
    coach_details = CoachDetails.query.filter_by(
        tennis_club_id=club.id
    ).all()
    
    # Create a dictionary for easy lookup
    coach_details_map = {details.user_id: details for details in coach_details}

    def get_status_data(details, status_type):
        """Helper function to get status data for template"""
        status_map = {
            'accreditation': {
                'field': 'accreditation_expiry',
                'label': 'Accreditation'
            },
            'dbs': {
                'field': 'dbs_expiry',
                'label': 'DBS Check'
            },
            'first_aid': {
                'field': 'first_aid_expiry',
                'label': 'First Aid'
            },
            'safeguarding': {
                'field': 'safeguarding_expiry',
                'label': 'Safeguarding'
            }
        }
        
        if not details:
            return {
                'color_class': 'bg-gray-50 border-gray-200 text-gray-500',
                'message': 'Not Set',
                'label': status_map[status_type]['label']
            }
        
        status_info = status_map[status_type]
        expiry_date = getattr(details, status_info['field'])
        
        if not expiry_date:
            return {
                'color_class': 'bg-gray-50 border-gray-200 text-gray-500',
                'message': 'Not Set',
                'label': status_info['label']
            }
        
        current_time = datetime.now(uk_timezone)
        if expiry_date.tzinfo != uk_timezone:
            expiry_date = expiry_date.astimezone(uk_timezone)
            
        days_until_expiry = (expiry_date - current_time).days
        
        if days_until_expiry < 0:
            color_class = 'bg-red-50 border-red-200 text-red-700'
            message = f'Expired {abs(days_until_expiry)} days ago'
        elif days_until_expiry <= 90:
            color_class = 'bg-yellow-50 border-yellow-200 text-yellow-700'
            message = f'Expires in {days_until_expiry} days'
        else:
            color_class = 'bg-green-50 border-green-200 text-green-700'
            message = f'Valid until {expiry_date.strftime("%d %b %Y")}'
            
        return {
            'color_class': color_class,
            'message': message,
            'label': status_info['label']
        }

    return render_template(
        'admin/manage_coaches.html',
        club=club,
        coaches=coaches,
        coach_details_map=coach_details_map,
        get_status_data=get_status_data,
        CoachQualification=CoachQualification,
        CoachRole=CoachRole
    )

@club_management.route('/manage/<int:club_id>/coaches/<int:coach_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_coach(club_id, coach_id):
    club = TennisClub.query.get_or_404(club_id)
    coach = User.query.get_or_404(coach_id)
    
    if current_user.tennis_club_id != club.id:
        flash('You can only manage coaches in your own tennis club', 'error')
        return redirect(url_for('main.dashboard'))
        
    details = CoachDetails.query.filter_by(user_id=coach_id, tennis_club_id=club_id).first()
    
    if request.method == 'POST':
        try:
            if not details:
                details = CoachDetails(user_id=coach_id, tennis_club_id=club_id)
                db.session.add(details)
            
            # Update fields from form
            details.coach_number = request.form.get('coach_number')
            if request.form.get('qualification'):
                details.qualification = CoachQualification[request.form.get('qualification')]
            if request.form.get('coach_role'):
                details.coach_role = CoachRole[request.form.get('coach_role')]
                
            # Parse dates
            details.date_of_birth = parse_birth_date(request.form.get('date_of_birth'))
            details.accreditation_expiry = parse_date(request.form.get('accreditation_expiry'))
            details.dbs_expiry = parse_date(request.form.get('dbs_expiry'))
            details.first_aid_expiry = parse_date(request.form.get('first_aid_expiry'))
            details.safeguarding_expiry = parse_date(request.form.get('safeguarding_expiry'))
            
            # Update other fields
            fields = [
                'contact_number', 'emergency_contact_name', 'emergency_contact_number',
                'address_line1', 'address_line2', 'city', 'postcode',
                'utr_number', 'bcta_accreditation', 'dbs_number', 
                'dbs_update_service_id'
            ]
            
            for field in fields:
                value = request.form.get(field)
                if value:  # Only set if value is not empty
                    setattr(details, field, value)
            
            db.session.commit()
            flash('Coach details updated successfully', 'success')
            return redirect(url_for('club_management.manage_coaches', club_id=club_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating coach details: {str(e)}', 'error')
    
    return render_template(
        'admin/edit_coach.html',
        club=club,
        coach=coach,
        details=details,
        coach_qualifications=CoachQualification,
        coach_roles=CoachRole
    )