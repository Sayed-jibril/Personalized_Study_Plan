from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
import sqlite3
import os
from chatbot import Chatbot

# New imports for email and token generation
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Replace with a secure key in production

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mrsar0812@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'csvy dwpe thcx jcnf'    # Replace with the app password

# Initialize Flask-Mail and itsdangerous serializer
mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

DATABASE = 'course_management.db'

# ============================
# Database Connection Function
# ============================
def connect_db():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None


# ============================
# HOME & LANDING
# ============================
@app.route('/')
def landing():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    elif session.get('student_logged_in'):
        return redirect(url_for('home'))  # or student dashboard
    return render_template('landing.html')


@app.route("/home")
def home():
    conn = connect_db()
    announcements = []
    current_semester = None
    exam_date = None

    if not conn:
        flash('Database connection failed. Using fallback data.', 'danger')
        # Fallback data
        announcements = [
            {"Title": "Fallback Announcement", "Message": "Database connection failed.", "Created_At": "N/A"}
        ]
        current_semester = {
            "SemesterName": "TBD",
            "Start_Date": "2025-09-10",
            "End_Date": "2025-12-20",
            "Exam_Date": "2025-12-15",
            "Is_Current": 1
        }
        exam_date = "2025-12-15"
        return render_template('home.html', announcements=announcements,
                               current_semester=current_semester, exam_date=exam_date)

    try:
        cursor = conn.cursor()

        # Fetch latest announcements (limit 5)
        cursor.execute("""
            SELECT AnnouncementID, Title, Message, Created_At
            FROM Announcements
            ORDER BY Created_At DESC
            LIMIT 5
        """)
        announcements = [
            {
                "AnnouncementID": row["AnnouncementID"],
                "Title": row["Title"],
                "Message": row["Message"],
                "Created_At": row["Created_At"]
            } for row in cursor.fetchall()
        ]

        # Fetch current semester info
        cursor.execute("""
            SELECT SemesterInfoID, SemesterName, Start_Date, End_Date, Exam_Date, Is_Current
            FROM SemesterInfo
            WHERE Is_Current = 1
            LIMIT 1
        """)
        sem_row = cursor.fetchone()

        if sem_row:
            current_semester = {
                "SemesterName": sem_row["SemesterName"],
                "Start_Date": sem_row["Start_Date"],
                "End_Date": sem_row["End_Date"],
                "Exam_Date": sem_row["Exam_Date"],
                "Is_Current": sem_row["Is_Current"]
            }
            exam_date = sem_row["Exam_Date"]
        else:
            flash('No current semester info available. Using fallback data.', 'warning')
            current_semester = {
                "SemesterName": "TBD",
                "Start_Date": "2025-09-10",
                "End_Date": "2025-12-20",
                "Exam_Date": "2025-12-15",
                "Is_Current": 1
            }
            exam_date = "2025-12-15"

    except sqlite3.Error as e:
        flash(f"Database error: {e}", 'danger')
        # Fallback data in case of errors
        announcements = [
            {"Title": "Error Occurred", "Message": str(e), "Created_At": "N/A"}
        ]
        current_semester = {
            "SemesterName": "TBD",
            "Start_Date": "2025-09-10",
            "End_Date": "2025-12-20",
            "Exam_Date": "2025-12-15",
            "Is_Current": 1
        }
        exam_date = "2025-12-15"

    finally:
        if conn:
            conn.close()

    return render_template('home.html', announcements=announcements,
                           current_semester=current_semester, exam_date=exam_date)


# Redirect '/' to '/home' for a consistent landing page
#@app.route('/')
#def landing():
#    return redirect(url_for('home'))

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

# ============================
# Student Registration Routes
# ============================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form['student_id'].strip()
        student_name = request.form['student_name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        profile_pic = request.files.get('profile_pic')

        # Basic validation
        if not all([student_id, student_name, email, password, confirm_password]):
            flash('Please fill out all required fields.', 'warning')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        conn = connect_db()
        if not conn:
            flash('Database connection failed.', 'danger')
            return redirect(url_for('register'))

        cursor = conn.cursor()
        # Check if student ID or email already exists
        cursor.execute("SELECT * FROM Users WHERE StudentID = ? OR Email = ?", (student_id, email))
        if cursor.fetchone():
            flash('Student ID or email already exists.', 'danger')
            conn.close()
            return redirect(url_for('register'))

        # Handle profile picture upload
        profile_pic_path = None
        if profile_pic:
            upload_folder = os.path.join('static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            filename = f"{student_id}_{profile_pic.filename}"
            profile_pic_path = os.path.join(upload_folder, filename)
            profile_pic.save(profile_pic_path)

        # Insert new user into the database
        cursor.execute("""
            INSERT INTO Users (StudentID, StudentName, Email, PasswordHash, ProfilePic)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, student_name, email, password, profile_pic_path))
        conn.commit()
        conn.close()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('student_login'))  # Redirect to student login

    return render_template('auth/register.html')

# ============================
# Student Authentication Routes
# ============================
@app.route('/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Users WHERE StudentID = ? AND PasswordHash = ?", (student_id, password))
            user = cursor.fetchone()
            conn.close()
            if user:
                # Store user details in session for better control
                session['student_logged_in'] = True
                session['student_id'] = user['StudentID']
                session['user_id'] = user['UserID']  # Added to prevent KeyError
                flash('Logged in successfully as student.', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials. Please try again.', 'danger')
        else:
            flash('Database connection failed.', 'danger')
    return render_template('auth/login.html')


@app.route('/logout')
def student_logout():
    session.pop('student_logged_in', None)
    session.pop('student_id', None)  # Clear student-specific session info
    flash('Logged out successfully.', 'success')
    return redirect(url_for('student_login'))  # Redirect to login or home as preferred


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').strip()

        # Validate if the email is empty
        if not email:
            flash('Please enter your email address.', 'warning')
            return redirect(url_for('forgot_password'))

        # Lookup user by email in database
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT UserID FROM Users WHERE Email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            user_id = user['UserID']
            # Generate a token with the user's email
            token = s.dumps(email, salt='password-recovery-salt')
            reset_link = url_for('reset_password', token=token, _external=True)

            try:
                # Send the reset link to user's email
                msg = Message("Password Reset Request",
                              sender=app.config['MAIL_USERNAME'],
                              recipients=[email])
                msg.body = f"To reset your password, click the following link: {reset_link}\n\nIf you did not make this request, please ignore this email."
                mail.send(msg)

                flash('A password reset link has been sent to your email.', 'info')
            except Exception as e:
                flash(f'Failed to send the reset email. Please try again later. Error: {str(e)}', 'danger')
        else:
            flash('The email address you entered is not registered with us.', 'warning')

        return redirect(url_for('forgot_password'))

    return render_template('auth/forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Verify token and extract email; expires after 3600 seconds (1 hour)
        email = s.loads(token, salt='password-recovery-salt', max_age=3600)
    except Exception as e:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('reset_password', token=token))

        # Update the user's password in the database
        # Use proper password hashing (e.g., bcrypt) in production
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE Users SET PasswordHash = ? WHERE Email = ?", (new_password, email))
        conn.commit()
        conn.close()

        flash('Your password has been updated. Please log in.', 'success')
        return redirect(url_for('student_login'))  # or appropriate login route

    return render_template('auth/reset_password.html', token=token)

# 📅 Study Planner Route
import random
@app.route('/study_planner', methods=['GET', 'POST'])
def study_planner():
    user_id = session.get('user_id')

    if not user_id:
        flash('Please log in to access your study planner.', 'warning')
        return redirect(url_for('student_login'))

    if request.method == 'POST':
        day = request.form.get('day')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        task = request.form.get('task')

        # Input validation to prevent empty submissions
        if not all([day, start_time, end_time, task]):
            flash('All fields are required to add a task.', 'danger')
            return redirect(url_for('study_planner'))

        conn = connect_db()
        cursor = conn.cursor()

        # Random Color for tasks (for visual differentiation)
        color = "#%06x" % random.randint(0, 0xFFFFFF)

        # Insert task into StudyPlan
        cursor.execute("""
            INSERT INTO StudyPlan (UserID, DayOfWeek, StartTime, EndTime, Task, Color)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, day, start_time, end_time, task, color))

        conn.commit()
        conn.close()

        flash('Task added successfully!', 'success')
        return redirect(url_for('study_planner'))

    # Fetch tasks for rendering
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM StudyPlan WHERE UserID = ?", (user_id,))
    study_plan = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template('study_planner.html', study_plan=study_plan)

# ❌ Delete Task
@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM StudyPlan WHERE PlanID = ?", (task_id,))
    conn.commit()
    conn.close()
    flash("Task deleted successfully!", "success")
    return redirect(url_for('study_planner'))

# ✏️ Edit Task
@app.route('/edit_task', methods=['POST'])
def edit_task():
    task_id = request.form.get('plan_id')  # Correct field for task ID
    task_name = request.form.get('task')   # Task name input
    day = request.form.get('day')          # Day selection
    start_time = request.form.get('start_time')  # Start time
    end_time = request.form.get('end_time')      # End time

    # Input validation
    if not all([task_id, task_name, day, start_time, end_time]):
        flash("All fields are required to update the task.", 'danger')
        return redirect(url_for('study_planner'))

    conn = connect_db()
    cursor = conn.cursor()

    # ✅ Ensure PlanID exists and update the correct task
    cursor.execute("""
        UPDATE StudyPlan
        SET Task = ?, DayOfWeek = ?, StartTime = ?, EndTime = ?
        WHERE PlanID = ?
    """, (task_name, day, start_time, end_time, task_id))

    conn.commit()
    conn.close()

    flash("Task updated successfully!", "success")
    return redirect(url_for('study_planner'))

# ============================
# Admin Authentication Routes
# ============================
# Route: Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT AdminID FROM Admins WHERE AdminUsername = ? AND AdminPassword = ?", (username, password))
            admin = cursor.fetchone()
            conn.close()
            if admin:
                session['admin_logged_in'] = True
                flash('Logged in successfully as admin.', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid credentials. Please try again.', 'danger')
        else:
            flash('Database connection failed.', 'danger')
    return render_template('admin/login.html')

# Route: Admin Logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin_login'))
# ============================
# Admin Dashboard Route
# ============================
# Route: Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to access the dashboard.', 'warning')
        return redirect(url_for('admin_login'))
    return render_template('admin/dashboard.html')

# ============================
# ADMIN: ANNOUNCEMENTS
# ============================
@app.route("/admin/announcements", methods=["GET", "POST"])
def admin_announcements():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to manage announcements.', 'warning')
        return redirect(url_for('admin_login'))

    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        # Updated path: "admin/admin_announcements.html"
        return render_template("admin/admin_announcements.html", announcements=[])

    cursor = conn.cursor()

    if request.method == "POST":
        new_title = request.form["title"].strip()
        new_message = request.form["message"].strip()
        if new_title and new_message:
            try:
                cursor.execute("""INSERT INTO Announcements (Title, Message) 
                                  VALUES (?, ?)""", (new_title, new_message))
                conn.commit()
                flash("Announcement added successfully!", "success")
            except sqlite3.Error as e:
                flash(f"Error adding announcement: {e}", "danger")
        else:
            flash("Title and Message cannot be empty.", "warning")

        return redirect(url_for("admin_announcements"))

    # If GET, show all announcements (newest first)
    cursor.execute("""SELECT AnnouncementID, Title, Message, Created_At
                      FROM Announcements
                      ORDER BY Created_At DESC""")
    ann_rows = cursor.fetchall()
    announcements = []
    for row in ann_rows:
        announcements.append({
            "AnnouncementID": row["AnnouncementID"],
            "Title": row["Title"],
            "Message": row["Message"],
            "Created_At": row["Created_At"]
        })

    conn.close()
    # Updated path: "admin/admin_announcements.html"
    return render_template("admin/admin_announcements.html", announcements=announcements)


@app.route("/admin/announcements/delete/<int:ann_id>", methods=["POST"])
def delete_announcement(ann_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to manage announcements.', 'warning')
        return redirect(url_for('admin_login'))

    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for("admin_announcements"))

    cursor = conn.cursor()
    try:
        cursor.execute("""DELETE FROM Announcements 
                          WHERE AnnouncementID = ?""",
                       (ann_id,))
        conn.commit()
        flash("Announcement deleted.", "info")
    except sqlite3.Error as e:
        flash(f"Error deleting announcement: {e}", "danger")
    conn.close()
    return redirect(url_for("admin_announcements"))


# ============================
# ADMIN: SEMESTER INFO
# ============================
@app.route("/admin/semesterinfo", methods=["GET", "POST"])
def admin_semesterinfo():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to manage semester info.', 'warning')
        return redirect(url_for('admin_login'))

    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        # Updated path: "admin/admin_semesterinfo.html"
        return render_template("admin/admin_semesterinfo.html", sem_info=None)

    cursor = conn.cursor()

    # Check if we have any current semester
    cursor.execute("""SELECT SemesterInfoID, SemesterName, Start_Date, End_Date, Exam_Date, Is_Current
                      FROM SemesterInfo
                      WHERE Is_Current = 1
                      LIMIT 1""")
    sem_row = cursor.fetchone()

    if request.method == "POST":
        semester_name = request.form["semester_name"].strip()
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        exam_date = request.form["exam_date"]

        if sem_row:
            # Update existing record
            sem_id = sem_row["SemesterInfoID"]
            try:
                cursor.execute("""UPDATE SemesterInfo
                                  SET SemesterName = ?, Start_Date = ?, End_Date = ?, Exam_Date = ?
                                  WHERE SemesterInfoID = ?""",
                               (semester_name, start_date, end_date, exam_date, sem_id))
                conn.commit()
                flash("Semester info updated!", "success")
            except sqlite3.Error as e:
                flash(f"Error updating semester info: {e}", "danger")
        else:
            # Insert a new row, mark is_current = 1
            try:
                cursor.execute("""INSERT INTO SemesterInfo 
                                  (SemesterName, Start_Date, End_Date, Exam_Date, Is_Current)
                                  VALUES (?, ?, ?, ?, 1)""",
                               (semester_name, start_date, end_date, exam_date))
                conn.commit()
                flash("Semester info created!", "success")
            except sqlite3.Error as e:
                flash(f"Error creating semester info: {e}", "danger")

        conn.close()
        return redirect(url_for("admin_semesterinfo"))

    # If GET, we show the form with existing data (if any)
    if sem_row:
        sem_info = {
            "SemesterInfoID": sem_row["SemesterInfoID"],
            "SemesterName": sem_row["SemesterName"],
            "Start_Date": sem_row["Start_Date"],
            "End_Date": sem_row["End_Date"],
            "Exam_Date": sem_row["Exam_Date"],
            "Is_Current": sem_row["Is_Current"]
        }
    else:
        sem_info = None

    conn.close()
    # Updated path: "admin/admin_semesterinfo.html"
    return render_template("admin/admin_semesterinfo.html", sem_info=sem_info)

# ============================
# ChatBot Route
# ============================
# Initialize your Chatbot instance
chatbot = Chatbot("knowledge_base.json")

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()  # Parse JSON data from the request
        user_input = data.get('user_input', '').strip()
        
        if not user_input:
            return jsonify({'response': "I didn't catch that. Could you please rephrase?"})
        
        # Get the chatbot's response
        response = chatbot.get_response(user_input)
        
        # If the bot doesn't know the answer, handle it based on user role
        if response == "I don't know the answer. Can you teach me?":
            if session.get('admin_logged_in'):
                # Admin is logged in, allow teaching mode
                chatbot.is_in_teach_mode = True
                chatbot.last_question = user_input  # Store the last question for teaching mode
                return jsonify({'response': response})
            else:
                # Student is logged in, display a message to contact the school
                return jsonify({'response': "Sorry, currently I don't know the answer. Ask your school to teach me."})
        
        return jsonify({'response': response})
    
    except Exception as e:
        # Log the error (optional)
        print(f"Error in /chat route: {e}")
        return jsonify({'response': "Sorry, I'm having trouble processing your request."}), 500

@app.route('/teach', methods=['POST'])
def teach():
    # Check if admin is logged in
    if not session.get('admin_logged_in'):
        return jsonify({'response': "Unauthorized access. Admins only."}), 403

    try:
        data = request.get_json()
        user_input = data.get('user_input', '').strip()  # The question to be taught
        new_answer = data.get('new_answer', '').strip()  # The answer to be taught
        
        if not user_input or not new_answer:
            return jsonify({'response': "Both question and answer are required to teach me."}), 400
        
        # Add new knowledge to the bot's knowledge base
        chatbot.add_new_knowledge(user_input, new_answer)
        
        # Reset teach mode
        chatbot.is_in_teach_mode = False
        chatbot.last_question = None  # Clear the last question
        
        return jsonify({'response': "Thank you for teaching me!"})
    
    except Exception as e:
        # Log the error (optional)
        print(f"Error in /teach route: {e}")
        return jsonify({'response': "Sorry, I'm unable to learn right now."}), 500

# ============================
# Manage Schools Routes
# ============================

# Route: Manage Schools
@app.route('/admin/manage_schools', methods=['GET', 'POST'])
def manage_schools():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Handle Adding a New School
        school_name = request.form['school_name'].strip()
        description = request.form['description'].strip()
        if school_name:
            try:
                cursor.execute("INSERT INTO Schools (SchoolName, Description) VALUES (?, ?)", (school_name, description))
                conn.commit()
                flash('School added successfully.', 'success')
            except sqlite3.IntegrityError:
                flash('School name already exists.', 'danger')
        else:
            flash('School name cannot be empty.', 'warning')
    
    # Fetch all schools
    cursor.execute("SELECT * FROM Schools ORDER BY SchoolName")
    schools = cursor.fetchall()
    conn.close()
    return render_template('admin/manage_schools.html', schools=schools)

# Route: Edit School
@app.route('/admin/edit_school/<int:school_id>', methods=['GET', 'POST'])
def edit_school(school_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_schools'))
    
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Handle Updating the School
        school_name = request.form['school_name'].strip()
        description = request.form['description'].strip()
        if school_name:
            try:
                cursor.execute("""
                    UPDATE Schools 
                    SET SchoolName = ?, Description = ?
                    WHERE SchoolID = ?
                """, (school_name, description, school_id))
                conn.commit()
                flash('School updated successfully.', 'success')
                return redirect(url_for('manage_schools'))
            except sqlite3.IntegrityError:
                flash('School name already exists.', 'danger')
        else:
            flash('School name cannot be empty.', 'warning')
    
    # Fetch the school details
    cursor.execute("SELECT * FROM Schools WHERE SchoolID = ?", (school_id,))
    school = cursor.fetchone()
    conn.close()
    
    if not school:
        flash('School not found.', 'danger')
        return redirect(url_for('manage_schools'))
    
    return render_template('admin/edit_school.html', school=school)

# Route: Delete School
@app.route('/admin/delete_school/<int:school_id>', methods=['POST'])
def delete_school(school_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_schools'))
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Schools WHERE SchoolID = ?", (school_id,))
        conn.commit()
        flash('School deleted successfully.', 'success')
    except sqlite3.Error as e:
        flash(f'Error deleting school: {e}', 'danger')
    conn.close()
    return redirect(url_for('manage_schools'))

# ============================
# Manage Programmes Routes
# ============================

# Route: Manage Programmes
@app.route('/admin/manage_programmes', methods=['GET', 'POST'])
def manage_programmes():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Handle Adding a New Programme
        programme_name = request.form['programme_name'].strip()
        school_id = request.form['school_id']
        description = request.form['description'].strip()
        if programme_name and school_id:
            try:
                cursor.execute("INSERT INTO Programmes (ProgrammeName, SchoolID, Description) VALUES (?, ?, ?)", 
                               (programme_name, school_id, description))
                conn.commit()
                flash('Programme added successfully.', 'success')
            except sqlite3.IntegrityError:
                flash('Programme name already exists.', 'danger')
        else:
            flash('Programme name and School selection are required.', 'warning')
    
    # Fetch all programmes with their school names
    query = """
        SELECT p.ProgrammeID, p.ProgrammeName, sch.SchoolName, p.Description
        FROM Programmes p
        JOIN Schools sch ON p.SchoolID = sch.SchoolID
        ORDER BY p.ProgrammeName
    """
    cursor.execute(query)
    programmes = cursor.fetchall()
    
    # Fetch all schools for dropdown
    cursor.execute("SELECT SchoolID, SchoolName FROM Schools ORDER BY SchoolName")
    schools = cursor.fetchall()
    conn.close()
    return render_template('admin/manage_programmes.html', programmes=programmes, schools=schools)

# Route: Edit Programme
@app.route('/admin/edit_programme/<int:programme_id>', methods=['GET', 'POST'])
def edit_programme(programme_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_programmes'))
    
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Handle Updating the Programme
        programme_name = request.form['programme_name'].strip()
        school_id = request.form['school_id']
        description = request.form['description'].strip()
        if programme_name and school_id:
            try:
                cursor.execute("""
                    UPDATE Programmes 
                    SET ProgrammeName = ?, SchoolID = ?, Description = ?
                    WHERE ProgrammeID = ?
                """, (programme_name, school_id, description, programme_id))
                conn.commit()
                flash('Programme updated successfully.', 'success')
                return redirect(url_for('manage_programmes'))
            except sqlite3.IntegrityError:
                flash('Programme name already exists.', 'danger')
        else:
            flash('Programme name and School selection are required.', 'warning')
    
    # Fetch the programme details
    cursor.execute("SELECT * FROM Programmes WHERE ProgrammeID = ?", (programme_id,))
    programme = cursor.fetchone()
    
    if not programme:
        flash('Programme not found.', 'danger')
        conn.close()
        return redirect(url_for('manage_programmes'))
    
    # Fetch all schools for dropdown
    cursor.execute("SELECT SchoolID, SchoolName FROM Schools ORDER BY SchoolName")
    schools = cursor.fetchall()
    conn.close()
    
    return render_template('admin/edit_programme.html', programme=programme, schools=schools)

# Route: Delete Programme
@app.route('/admin/delete_programme/<int:programme_id>', methods=['POST'])
def delete_programme(programme_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_programmes'))
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Programmes WHERE ProgrammeID = ?", (programme_id,))
        conn.commit()
        flash('Programme deleted successfully.', 'success')
    except sqlite3.Error as e:
        flash(f'Error deleting programme: {e}', 'danger')
    conn.close()
    return redirect(url_for('manage_programmes'))

# ============================
# Manage Terms Routes
# ============================

# Route: Manage Terms
@app.route('/admin/manage_terms', methods=['GET', 'POST'])
def manage_terms():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Handle Adding a New Term
        term_number = request.form['term_number']
        description = request.form['description'].strip()
        if term_number:
            try:
                cursor.execute("INSERT INTO Terms (TermNumber, Description) VALUES (?, ?)", 
                               (term_number, description))
                conn.commit()
                flash('Term added successfully.', 'success')
            except sqlite3.IntegrityError:
                flash('Term number already exists.', 'danger')
        else:
            flash('Term number is required.', 'warning')
    
    # Fetch all terms
    cursor.execute("SELECT * FROM Terms ORDER BY TermNumber")
    terms = cursor.fetchall()
    conn.close()
    return render_template('admin/manage_terms.html', terms=terms)

# Route: Edit Term
@app.route('/admin/edit_term/<int:term_id>', methods=['GET', 'POST'])
def edit_term(term_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_terms'))
    
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Handle Updating the Term
        term_number = request.form['term_number'].strip()
        description = request.form['description'].strip()
        if term_number:
            try:
                cursor.execute("""
                    UPDATE Terms 
                    SET TermNumber = ?, Description = ?
                    WHERE TermID = ?
                """, (term_number, description, term_id))
                conn.commit()
                flash('Term updated successfully.', 'success')
                return redirect(url_for('manage_terms'))
            except sqlite3.IntegrityError:
                flash('Term number already exists.', 'danger')
        else:
            flash('Term number is required.', 'warning')
    
    # Fetch the term details
    cursor.execute("SELECT * FROM Terms WHERE TermID = ?", (term_id,))
    term = cursor.fetchone()
    conn.close()
    
    if not term:
        flash('Term not found.', 'danger')
        return redirect(url_for('manage_terms'))
    
    return render_template('admin/edit_term.html', term=term)

# Route: Delete Term
@app.route('/admin/delete_term/<int:term_id>', methods=['POST'])
def delete_term(term_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_terms'))
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Terms WHERE TermID = ?", (term_id,))
        conn.commit()
        flash('Term deleted successfully.', 'success')
    except sqlite3.Error as e:
        flash(f'Error deleting term: {e}', 'danger')
    conn.close()
    return redirect(url_for('manage_terms'))

# ============================
# Manage Semesters Routes
# ============================

# Route: Manage Semesters
@app.route('/admin/manage_semesters', methods=['GET', 'POST'])
def manage_semesters():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    cursor = conn.cursor()
    
    # Fetch all terms for dropdown
    cursor.execute("SELECT TermID, TermNumber, Description FROM Terms ORDER BY TermNumber")
    terms = cursor.fetchall()
    
    if request.method == 'POST':
        # Handle Adding a New Semester
        term_id = request.form['term_id']
        semester_number = request.form['semester_number']
        description = request.form['description'].strip()
        if term_id and semester_number:
            try:
                cursor.execute("""
                    INSERT INTO Semesters (TermID, SemesterNumber, Description)
                    VALUES (?, ?, ?)
                """, (term_id, semester_number, description))
                conn.commit()
                flash('Semester added successfully.', 'success')
            except sqlite3.IntegrityError:
                flash('Semester number already exists for the selected term.', 'danger')
        else:
            flash('Term and Semester number are required.', 'warning')
    
    # Fetch all semesters with their terms
    query = """
        SELECT sem.SemesterID, sem.SemesterNumber, sem.Description, t.TermNumber, t.Description as TermDesc
        FROM Semesters sem
        JOIN Terms t ON sem.TermID = t.TermID
        ORDER BY t.TermNumber, sem.SemesterNumber
    """
    cursor.execute(query)
    semesters = cursor.fetchall()
    conn.close()
    return render_template('admin/manage_semesters.html', semesters=semesters, terms=terms)

# Route: Edit Semester
@app.route('/admin/edit_semester/<int:semester_id>', methods=['GET', 'POST'])
def edit_semester(semester_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_semesters'))
    
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Handle Updating the Semester
        term_id = request.form['term_id']
        semester_number = request.form['semester_number']
        description = request.form['description'].strip()
        if term_id and semester_number:
            try:
                cursor.execute("""
                    UPDATE Semesters 
                    SET TermID = ?, SemesterNumber = ?, Description = ?
                    WHERE SemesterID = ?
                """, (term_id, semester_number, description, semester_id))
                conn.commit()
                flash('Semester updated successfully.', 'success')
                return redirect(url_for('manage_semesters'))
            except sqlite3.IntegrityError:
                flash('Semester number already exists for the selected term.', 'danger')
        else:
            flash('Term and Semester number are required.', 'warning')
    
    # Fetch the semester details
    cursor.execute("SELECT * FROM Semesters WHERE SemesterID = ?", (semester_id,))
    semester = cursor.fetchone()
    
    if not semester:
        flash('Semester not found.', 'danger')
        conn.close()
        return redirect(url_for('manage_semesters'))
    
    # Fetch all terms for dropdown
    cursor.execute("SELECT TermID, TermNumber, Description FROM Terms ORDER BY TermNumber")
    terms = cursor.fetchall()
    conn.close()
    
    return render_template('admin/edit_semester.html', semester=semester, terms=terms)

# Route: Delete Semester
@app.route('/admin/delete_semester/<int:semester_id>', methods=['POST'])
def delete_semester(semester_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_semesters'))
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Semesters WHERE SemesterID = ?", (semester_id,))
        conn.commit()
        flash('Semester deleted successfully.', 'success')
    except sqlite3.Error as e:
        flash(f'Error deleting semester: {e}', 'danger')
    conn.close()
    return redirect(url_for('manage_semesters'))

# ============================
# Manage Courses Routes
# ============================
@app.route('/admin/manage_courses', methods=['GET', 'POST'])
def manage_courses():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    cursor = conn.cursor()

    # Retrieve multiple sorting criteria, with a default fallback
    selected_sort_fields = request.args.getlist('sort_by')
    if not selected_sort_fields:
        selected_sort_fields = ['c.CourseCode']  # default field with table alias

    # Define allowed sorting fields to prevent SQL injection
    allowed_sort_fields = {
        'c.CourseCode', 'sch.SchoolName', 'sem.Description', 'p.ProgrammeName', 'c.CreditHours',
        't.TermNumber', 'sem.SemesterNumber'
    }
    # Filter and sanitize user-provided fields
    sort_fields = [field for field in selected_sort_fields if field in allowed_sort_fields]
    if not sort_fields:
        sort_fields = ['c.CourseCode']

    # Retrieve ordering direction
    order = request.args.get('order', 'ASC')
    # Build dynamic ORDER BY clause from allowed sort fields
    order_by_clause = ", ".join(sort_fields) + " " + order

    # Retrieve optional filters for School, Programme, Term and Semester
    filter_school = request.args.get('filter_school')
    filter_programme = request.args.get('filter_programme')
    filter_term = request.args.get('filter_term')
    filter_semester = request.args.get('filter_semester')

    if request.method == 'POST':
        # Handle Adding a New Course
        course_code = request.form['course_code'].strip()
        course_name = request.form['course_name'].strip()
        credit_hours = request.form['credit_hours']
        programme_id = request.form['programme_id']
        semester_id = request.form['semester_id']
        category = request.form['category']
        prerequisites = request.form.getlist('prerequisites')  # List of CourseCodes
        
        if course_code and course_name and credit_hours and programme_id and semester_id and category:
            try:
                # Insert the new course
                cursor.execute(""" 
                    INSERT INTO Courses (CourseCode, CourseName, CreditHours, ProgrammeID, SemesterID, Category)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (course_code, course_name, credit_hours, programme_id, semester_id, category))
                conn.commit()

                # Get the CourseID of the newly inserted course
                cursor.execute("SELECT CourseID FROM Courses WHERE CourseCode = ?", (course_code,))
                course = cursor.fetchone()
                if course:
                    course_id = course['CourseID']
                    # Insert prerequisites
                    for prereq_code in prerequisites:
                        cursor.execute("SELECT CourseID FROM Courses WHERE CourseCode = ?", (prereq_code,))
                        prereq = cursor.fetchone()
                        if prereq:
                            cursor.execute("""
                                INSERT INTO Prerequisites (CourseID, PrerequisiteID)
                                VALUES (?, ?)
                            """, (course_id, prereq['CourseID']))
                    conn.commit()
                    flash('Course added successfully with prerequisites.', 'success')
                else:
                    flash('Failed to retrieve the newly added course.', 'danger')
            except sqlite3.IntegrityError:
                flash('Course code already exists.', 'danger')
        else:
            flash('All course fields are required.', 'warning')

    # Build base query with necessary joins
    base_query = """
        SELECT c.CourseID, c.CourseCode, c.CourseName, c.CreditHours, c.Category,
               p.ProgrammeName, sch.SchoolName, sem.Description as SemesterDesc,
               t.TermNumber, sem.SemesterNumber
        FROM Courses c
        JOIN Programmes p ON c.ProgrammeID = p.ProgrammeID
        JOIN Schools sch ON p.SchoolID = sch.SchoolID
        JOIN Semesters sem ON c.SemesterID = sem.SemesterID
        JOIN Terms t ON sem.TermID = t.TermID
    """

    # Build filtering conditions dynamically
    conditions = []
    params = []
    if filter_school:
        conditions.append("sch.SchoolID = ?")
        params.append(filter_school)
    if filter_programme:
        conditions.append("p.ProgrammeID = ?")
        params.append(filter_programme)
    if filter_term:
        conditions.append("t.TermNumber = ?")
        params.append(filter_term)
    if filter_semester:
        conditions.append("sem.SemesterNumber = ?")
        params.append(filter_semester)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # Combine base query, filters, and ordering
    final_query = f"{base_query} {where_clause} ORDER BY {order_by_clause}"

    cursor.execute(final_query, params)
    courses = cursor.fetchall()

    # Fetch all programmes for dropdown
    cursor.execute("SELECT ProgrammeID, ProgrammeName FROM Programmes ORDER BY ProgrammeName")
    programmes = cursor.fetchall()

    # Fetch all semesters for dropdown
    cursor.execute("SELECT SemesterID, Description FROM Semesters ORDER BY SemesterID")
    semesters = cursor.fetchall()

    # Fetch all existing courses for prerequisites selection
    cursor.execute("SELECT CourseCode, CourseName FROM Courses ORDER BY CourseCode")
    existing_courses = cursor.fetchall()

    conn.close()

    return render_template(
        'admin/manage_courses.html', 
        courses=courses, 
        programmes=programmes, 
        semesters=semesters, 
        existing_courses=existing_courses, 
        sort_by=selected_sort_fields, 
        order=order
    )

# Route: Edit Course
@app.route('/admin/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_courses'))
    
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Handle Updating the Course
        course_code = request.form['course_code'].strip()
        course_name = request.form['course_name'].strip()
        credit_hours = request.form['credit_hours']
        programme_id = request.form['programme_id']
        semester_id = request.form['semester_id']
        category = request.form['category']
        prerequisites = request.form.getlist('prerequisites')  # List of CourseCodes
        
        if course_code and course_name and credit_hours and programme_id and semester_id and category:
            try:
                # Update the course details
                cursor.execute("""
                    UPDATE Courses 
                    SET CourseCode = ?, CourseName = ?, CreditHours = ?, ProgrammeID = ?, SemesterID = ?, Category = ?
                    WHERE CourseID = ?
                """, (course_code, course_name, credit_hours, programme_id, semester_id, category, course_id))
                conn.commit()
                
                # Remove existing prerequisites
                cursor.execute("DELETE FROM Prerequisites WHERE CourseID = ?", (course_id,))
                
                # Insert new prerequisites
                for prereq_code in prerequisites:
                    cursor.execute("SELECT CourseID FROM Courses WHERE CourseCode = ?", (prereq_code,))
                    prereq = cursor.fetchone()
                    if prereq:
                        cursor.execute("""
                            INSERT INTO Prerequisites (CourseID, PrerequisiteID)
                            VALUES (?, ?)
                        """, (course_id, prereq['CourseID']))
                conn.commit()
                flash('Course updated successfully with prerequisites.', 'success')
                return redirect(url_for('manage_courses'))
            except sqlite3.IntegrityError:
                flash('Course code already exists.', 'danger')
        else:
            flash('All course fields are required.', 'warning')
    
    # Fetch the course details
    cursor.execute("SELECT * FROM Courses WHERE CourseID = ?", (course_id,))
    course = cursor.fetchone()
    
    if not course:
        flash('Course not found.', 'danger')
        conn.close()
        return redirect(url_for('manage_courses'))
    
    # Fetch all programmes for dropdown
    cursor.execute("SELECT ProgrammeID, ProgrammeName FROM Programmes ORDER BY ProgrammeName")
    programmes = cursor.fetchall()
    
    # Fetch all semesters for dropdown
    cursor.execute("SELECT SemesterID, Description FROM Semesters ORDER BY SemesterID")
    semesters = cursor.fetchall()
    
    # Fetch all existing courses except the current one for prerequisites selection
    cursor.execute("SELECT CourseCode, CourseName FROM Courses WHERE CourseID != ? ORDER BY CourseCode", (course_id,))
    existing_courses = cursor.fetchall()
    
    # Fetch current prerequisites
    cursor.execute("""
        SELECT p.CourseCode
        FROM Prerequisites pr
        JOIN Courses p ON pr.PrerequisiteID = p.CourseID
        WHERE pr.CourseID = ?
    """, (course_id,))
    current_prereqs = [row['CourseCode'] for row in cursor.fetchall()]
    
    conn.close()
    return render_template('admin/edit_course.html', course=course, programmes=programmes, semesters=semesters, existing_courses=existing_courses, current_prereqs=current_prereqs)

# Route: Delete Course
@app.route('/admin/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to perform this action.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_courses'))
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Courses WHERE CourseID = ?", (course_id,))
        conn.commit()
        flash('Course deleted successfully.', 'success')
    except sqlite3.Error as e:
        flash(f'Error deleting course: {e}', 'danger')
    conn.close()
    return redirect(url_for('manage_courses'))

# ============================
# Update Prerequisites Route
# ============================

# Route: Update Prerequisites for a Course
@app.route('/admin/update_prerequisites/<int:course_id>', methods=['GET', 'POST'])
def update_prerequisites(course_id):
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('manage_courses'))
    
    cursor = conn.cursor()
    
    # Fetch course details
    cursor.execute("SELECT CourseCode, CourseName FROM Courses WHERE CourseID = ?", (course_id,))
    course = cursor.fetchone()
    if not course:
        flash('Course not found.', 'danger')
        conn.close()
        return redirect(url_for('manage_courses'))
    
    # Fetch all existing courses except the current one for prerequisites selection
    cursor.execute("SELECT CourseID, CourseCode, CourseName FROM Courses WHERE CourseID != ? ORDER BY CourseCode", (course_id,))
    all_courses = cursor.fetchall()
    
    # Fetch current prerequisites
    cursor.execute("""
        SELECT p.CourseCode
        FROM Prerequisites pr
        JOIN Courses p ON pr.PrerequisiteID = p.CourseID
        WHERE pr.CourseID = ?
    """, (course_id,))
    current_prereqs = [row['CourseCode'] for row in cursor.fetchall()]
    
    if request.method == 'POST':
        # Get selected prerequisites from the form
        selected_prereqs = request.form.getlist('prerequisites')
        
        try:
            # Remove all existing prerequisites
            cursor.execute("DELETE FROM Prerequisites WHERE CourseID = ?", (course_id,))
            
            # Add new prerequisites
            for prereq_code in selected_prereqs:
                cursor.execute("SELECT CourseID FROM Courses WHERE CourseCode = ?", (prereq_code,))
                prereq = cursor.fetchone()
                if prereq:
                    cursor.execute("""
                        INSERT INTO Prerequisites (CourseID, PrerequisiteID)
                        VALUES (?, ?)
                    """, (course_id, prereq['CourseID']))
            conn.commit()
            flash('Prerequisites updated successfully.', 'success')
            return redirect(url_for('manage_courses'))
        except sqlite3.Error as e:
            flash(f'Error updating prerequisites: {e}', 'danger')
            conn.rollback()
    
    conn.close()
    return render_template('admin/update_prerequisites.html', course=course, all_courses=all_courses, current_prereqs=current_prereqs)

# ============================
# Manage Programmes Routes
# ============================

# If previously included 'manage_subjects', it's now 'manage_programmes', which was covered above.

# ============================
# User Routes
# ============================
@app.route('/get_programmes/<int:school_id>', methods=['GET'])
def get_programmes(school_id):
    conn = connect_db()
    if not conn:
        return jsonify({'programmes': []})  # Return empty if the database connection fails

    cursor = conn.cursor()
    cursor.execute("SELECT ProgrammeID, ProgrammeName FROM Programmes WHERE SchoolID = ?", (school_id,))
    programmes = cursor.fetchall()

    conn.close()
    
    # Return programmes as JSON
    return jsonify({'programmes': [{'ProgrammeID': programme[0], 'ProgrammeName': programme[1]} for programme in programmes]})

# Remove or comment out the old index() route
# @app.route('/', methods=['GET', 'POST'])
# def index():
#     ...

# New route for Course Recommendation
@app.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return render_template('index.html', schools=[], programmes=[], subjects=[])

    cursor = conn.cursor()

    # Fetch all schools for dropdown
    cursor.execute("SELECT SchoolID, SchoolName FROM Schools ORDER BY SchoolName")
    schools = cursor.fetchall()

    programmes = []
    school_id = None
    if request.method == 'POST':
        # Get user selections from form
        school_id = request.form.get('school')
        programme_id = request.form.get('programme')
        year = request.form.get('year')
        semester = request.form.get('semester')

        if school_id and programme_id:
            # Fetch programmes based on selected school
            cursor.execute("SELECT ProgrammeID, ProgrammeName FROM Programmes WHERE SchoolID = ?", (school_id,))
            programmes = cursor.fetchall()

        # If school, programme, year, and semester are selected, redirect to the next page
        if school_id and programme_id and year and semester:
            return redirect(url_for(
                'select_prereqs',
                school_id=school_id,
                programme_id=programme_id,
                year=year,
                semester=semester
            ))
        else:
            flash('Please select School, Programme, Year, and Semester.', 'warning')

    # If GET request, check if a school was already selected
    elif request.method == 'GET':
        school_id = request.args.get('school')
        if school_id:
            cursor.execute("SELECT ProgrammeID, ProgrammeName FROM Programmes WHERE SchoolID = ?", (school_id,))
            programmes = cursor.fetchall()

    conn.close()
    return render_template('index.html', schools=schools, programmes=programmes)

# Route: Select Completed Prerequisites
@app.route('/select_prereqs/<int:school_id>/<int:programme_id>/<int:year>/<int:semester>', methods=['GET', 'POST'])
def select_prereqs(school_id, programme_id, year, semester):
    conn = connect_db()
    if not conn:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('index'))
    
    cursor = conn.cursor()
    
    # Fetch available courses based on school, programme, year, and semester
    # Now we join Terms (t) and filter by t.TermNumber = 'year' and sem.SemesterNumber = 'semester'.
    query = """
        SELECT c.CourseID, c.CourseCode, c.CourseName, c.CreditHours, c.Category,
               p.ProgrammeName, sch.SchoolName, sem.Description as SemesterDesc
        FROM Courses c
        JOIN Programmes p ON c.ProgrammeID = p.ProgrammeID
        JOIN Schools sch ON p.SchoolID = sch.SchoolID
        JOIN Semesters sem ON c.SemesterID = sem.SemesterID
        JOIN Terms t ON sem.TermID = t.TermID
        WHERE p.ProgrammeID = ?
          AND t.TermNumber = ?
          AND sem.SemesterNumber = ?
        ORDER BY c.CourseCode
    """
    # We pass programme_id, year (TermNumber), and semester (SemesterNumber) to the query
    cursor.execute(query, (programme_id, year, semester))
    courses = cursor.fetchall()
    
    # Fetch the programme details
    cursor.execute("SELECT ProgrammeID, ProgrammeName FROM Programmes WHERE ProgrammeID = ?", (programme_id,))
    programme = cursor.fetchone()
    
    courses_with_prereqs = []
    
    for course in courses:
        # Fetch prerequisites for each course
        prereq_query = """
            SELECT p.CourseCode, p.CourseName
            FROM Prerequisites pr
            JOIN Courses p ON pr.PrerequisiteID = p.CourseID
            WHERE pr.CourseID = ?
        """
        cursor.execute(prereq_query, (course['CourseID'],))
        prerequisites = cursor.fetchall()
        if prerequisites:
            prereq_str = "; ".join([f"{prereq['CourseCode']}: {prereq['CourseName']}" for prereq in prerequisites])
        else:
            prereq_str = "None"
        courses_with_prereqs.append({
            'CourseID': course['CourseID'],
            'CourseCode': course['CourseCode'],
            'CourseName': course['CourseName'],
            'CreditHours': course['CreditHours'],
            'Category': course['Category'] if course['Category'] else "Core",
            'Prerequisites': prereq_str,
            'ProgrammeName': programme['ProgrammeName'],
            'SchoolName': course['SchoolName']
        })
    
    if request.method == 'POST':
        # Collect user's completed prerequisites from form
        completed = {}
        for course in courses_with_prereqs:
            if course['Prerequisites'] != "None":
                # Get list of completed prerequisites for this course
                completed_prereqs = request.form.getlist(course['CourseCode'])
                completed[course['CourseCode']] = completed_prereqs
            else:
                completed[course['CourseCode']] = []
        
        # Generate course recommendations based on completed prerequisites
        eligible_courses = []
        ineligible_courses = []
        
        for course in courses_with_prereqs:
            if course['Prerequisites'] == "None":
                eligible_courses.append(course)
            else:
                prereq_codes = [prereq.split(":")[0].strip() for prereq in course['Prerequisites'].split(";")]
                user_completed = completed.get(course['CourseCode'], [])
                if set(prereq_codes).issubset(set(user_completed)):
                    eligible_courses.append(course)
                else:
                    missing = set(prereq_codes) - set(user_completed)
                    ineligible_courses.append({
                        'CourseCode': course['CourseCode'],
                        'CourseName': course['CourseName'],
                        'MissingPrerequisites': ", ".join(missing)
                    })
        
        conn.close()
        return render_template('recommendations.html', courses=eligible_courses, ineligible=ineligible_courses)
    
    conn.close()
    return render_template(
        'select_prereqs.html', 
        courses=courses_with_prereqs, 
        year=year, 
        semester=semester, 
        school_id=school_id, 
        programme_id=programme_id, 
        selected_programme=programme
    )

# ============================
# Run the Flask Application
# ============================

if __name__ == '__main__':
    app.run()