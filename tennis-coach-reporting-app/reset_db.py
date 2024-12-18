from app import create_app, db
from app.models import User, TennisGroup, TeachingPeriod, Student, Report, TennisClub, UserRole
from datetime import datetime

def reset_database():
    app = create_app()
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating tables...")
        db.create_all()
        
        # Create initial tennis club
        wilton_club = TennisClub(
            name="Wilton Tennis Club",
            subdomain="wilton"
        )
        
        try:
            db.session.add(wilton_club)
            db.session.commit()
            print("Created tennis club")
            
            # Create initial tennis groups
            groups = [
                TennisGroup(
                    name="Red 1", 
                    description="Beginners 4-6 years",
                    tennis_club_id=wilton_club.id
                ),
                TennisGroup(
                    name="Red 2", 
                    description="Advanced Beginners 5-7 years",
                    tennis_club_id=wilton_club.id
                ),
                TennisGroup(
                    name="Orange", 
                    description="Intermediate 7-9 years",
                    tennis_club_id=wilton_club.id
                ),
                TennisGroup(
                    name="Green", 
                    description="Advanced 9-10 years",
                    tennis_club_id=wilton_club.id
                )
            ]
            
            # Create terms
            terms = [
                TeachingPeriod(
                    name="Spring 2024",
                    start_date=datetime(2024, 1, 8),
                    end_date=datetime(2024, 3, 28),
                    tennis_club_id=wilton_club.id
                ),
                TeachingPeriod(
                    name="Summer 2024",
                    start_date=datetime(2024, 4, 15),
                    end_date=datetime(2024, 7, 19),
                    tennis_club_id=wilton_club.id
                ),
                TeachingPeriod(
                    name="Autumn 2024",
                    start_date=datetime(2024, 9, 2),
                    end_date=datetime(2024, 12, 13),
                    tennis_club_id=wilton_club.id
                )
            ]
            
            # Add all to database
            for group in groups:
                db.session.add(group)
            for term in terms:
                db.session.add(term)
            
            db.session.commit()
            print("Successfully initialized database with:", 
                  f"\n- 1 Tennis Club (Wilton)",
                  f"\n- {len(groups)} Groups",
                  f"\n- {len(terms)} Terms")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            raise

if __name__ == "__main__":
    reset_database()