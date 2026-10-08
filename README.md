---
# Personalized Study Plan System

The **Personalized Study Plan System** is a Flask-based web application designed to assist students and administrators in managing personalized course recommendations, weekly study plans, and administrative tasks efficiently. It features a chatbot for course-related queries, making the academic planning experience seamless and interactive.
---

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Demo](#demo)
- [Installation](#installation)
- [Usage](#usage)
  - [Student User Guide](#student-user-guide)
  - [Administrator User Guide](#administrator-user-guide)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## Features

- **Personalized Course Recommendations:** Automated prerequisite checks to suggest eligible courses.
- **Weekly Study Planner:** Manage tasks and schedules through an intuitive calendar interface.
- **Administrative Management:** Manage schools, programs, courses, semesters, and announcements.
- **Chatbot Support:** Interactive chatbot to answer course-related queries and learn new answers in teaching mode.
- **User Authentication:** Secure login and registration for both students and administrators.
- **Password Recovery:** Forgot password functionality for students.

---

## System Requirements

- **Web Browser:** Latest version of Chrome, Firefox, Edge, or Safari
- **Internet Access**

---

## Demo

Access the live application at:  
[https://personalizedstudyplan.onrender.com](https://personalizedstudyplan.onrender.com)

---

## Installation

To run the Personalized Study Plan System locally, follow these steps:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/shahabaalam/render_crs.git
   cd render_crs
   ```

2. **Create a virtual environment (optional but recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   > **Note:** Ensure you have Flask installed. Additional dependencies might be required depending on the project.

4. **Run the application:**
   ```bash
   python app.py
   ```
   The application should now be running on [http://localhost:5000](http://localhost:5000).

---

## Usage

### Student User Guide

1. **Accessing the Application:**

   - Open your web browser and navigate to [https://personalizedstudyplan.onrender.com](https://personalizedstudyplan.onrender.com).
   - On the landing page, choose between Student Login, Create Account, or Admin Login.

2. **Student Registration:**

   - Click on **Create Account** on the landing page.
   - Fill in the required details: Student ID, Name, Email, Password, and optionally upload a profile picture.
   - Click **Register** and then log in with your credentials.

3. **Student Login:**

   - Select **Student Login**, enter your Student ID and Password, and click **Login**.
   - Upon success, you'll be redirected to your Home Page.

4. **Home Page Features:**

   - View recent announcements, current semester details, and upcoming exam countdowns.
   - Navigate using the sidebar to access Course Recommendations, Study Planner, and Chatbot Support.

5. **Course Recommendations:**

   - Select **Course Recommendation** from the sidebar.
   - Choose your School, Programme, Year, and Semester.
   - Mark completed prerequisites and click **Get Recommendations**.
   - View recommended courses and courses that cannot be registered for due to missing prerequisites.

6. **Weekly Study Planner:**

   - Access the **Study Planner** via the sidebar.
   - Add new tasks by specifying the day, start/end time, and task description.
   - Edit or delete tasks as needed.

7. **Chatbot Support:**

   - Use **Chatbot Support** for course queries.
   - If the chatbot cannot answer, and responds with “I don’t know the answer. Can you teach me?”, contact an admin to update its knowledge base.

8. **Password Recovery:**

   - From the Student Login page, click **Forgot Password?**
   - Enter your email and follow the password reset instructions.

9. **Logout:**
   - Click on **Logout** to end your session and return to the landing page.

### Administrator User Guide

1. **Admin Login:**

   - Click **Admin Login** on the landing page or navigate to `/admin/login`.
   - Enter the provided administrator username and password.

2. **Admin Dashboard:**

   - Access management sections for Schools, Programmes, Terms, Semesters, Courses, and Announcements.

3. **Managing Entities:**

   - **Schools:** Add, edit, or delete schools at `/admin/manage_schools`.
   - **Programmes:** Manage programmes at `/admin/manage_programmes`.
   - **Terms and Semesters:** Manage academic terms and semesters at `/admin/manage_terms` and `/admin/manage_semesters`.
   - **Courses:** Add, edit, or delete courses at `/admin/manage_courses`. Set prerequisites, sort, and filter courses.
   - **Announcements:** Add or delete announcements at `/admin/announcements`.
   - **Semester Info:** Update current semester details at `/admin/semesterinfo`.

4. **Chatbot Teaching Mode:**

   - When the chatbot requests teaching mode, access the `/teach` route.
   - Provide the correct answers in JSON format to update the knowledge base.

5. **Admin Logout:**
   - Use the **Logout** button on the dashboard to end the session.

---

## Project Structure

```plaintext
├── static
│   ├── images
│   ├── uploads
│   └── styles.css
├── templates
│   ├── admin
│   │   ├── add_course.html
│   │   ├── admin_announcements.html
│   │   ├── admin_semesterinfo.html
│   │   ├── dashboard.html
│   │   ├── edit_course.html
│   │   ├── edit_programme.html
│   │   ├── edit_school.html
│   │   ├── edit_semester.html
│   │   ├── edit_term.html
│   │   ├── login.html
│   │   ├── manage_courses.html
│   │   ├── manage_programmes.html
│   │   ├── manage_schools.html
│   │   ├── manage_semesters.html
│   │   ├── manage_terms.html
│   │   ├── manage_users.html
│   │   └── update_prerequisites.html
│   ├── auth
│   │   ├── forgot_password.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── reset_password.html
│   ├── base.html
│   ├── chatbot.html
│   ├── home.html
│   ├── index.html
│   ├── landing.html
│   ├── recommendations.html
│   ├── select_prereqs.html
│   └── study_planner.html
├── .gitignore
├── app.py
├── chatbot.py
├── course_management.db
└── README.md
```

---

## Troubleshooting

- **Cannot Log In:**
  - Ensure correct credentials. Use the forgot password feature if needed.
- **No Announcements Displayed:**
  - Verify that announcements exist in the database.
- **Prerequisite Not Recognized:**
  - Check the course code for prerequisites in the admin panel.
- **Chatbot Doesn’t Recognize Query:**
  - The question may be absent from `knowledge_base.json`. An admin can teach the chatbot.
- **Database Connection Error:**
  - Check permissions for `course_management.db` and ensure the Flask app has read/write access.

---
