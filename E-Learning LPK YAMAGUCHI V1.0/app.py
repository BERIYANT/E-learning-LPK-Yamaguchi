from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import mysql.connector, os

app = Flask(__name__)
app.secret_key = "rahasia-super-aman"

# Upload config
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# === KONFIGURASI DATABASE ===
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'lms_jepang'
}

# === HELPERS ===
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# === HELPER DATABASE ===
def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(**db_config)
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop('db', None)
    if db:
        db.close()

# === USER SESSION ===
@app.before_request
def load_user():
    user_id = session.get("user_id")
    if user_id:
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        g.user = cur.fetchone()
    else:
        g.user = None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not g.user:
            flash("Silakan login terlebih dahulu.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    """Decorator untuk memastikan user adalah admin"""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not g.user:
            flash("Silakan login terlebih dahulu.")
            return redirect(url_for('login'))
        
        user_role = g.user.get('role', '')
        
        if user_role != 'admin':
            flash("Akses ditolak. Hanya admin yang dapat mengakses halaman ini.")
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return wrapper

def class_required(f):
    """Decorator untuk memastikan sensei sudah memilih kelas"""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user.get('role') == 'sensei' and not session.get('selected_class_id'):
            flash("Silakan pilih kelas terlebih dahulu.")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return wrapper

# === ROUTES UTAMA ===
@app.route('/')
def index():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM materials ORDER BY created_at DESC")
    materials = cur.fetchall()
    return render_template('index.html', materials=materials)


@app.route('/register', methods=['GET', 'POST'])
def register():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM classes ORDER BY id")
    classes = cur.fetchall()

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = generate_password_hash(request.form['password'])
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'student')
        class_id = request.form.get('class_id')

        cur2 = db.cursor()
        try:
            cur2.execute("INSERT INTO users (username, password, role, full_name) VALUES (%s, %s, %s, %s)",
                         (username, password, role, full_name))
            user_id = cur2.lastrowid

            # enroll otomatis untuk siswa
            if class_id and role == 'student':
                cur2.execute("INSERT INTO enrollments (user_id, class_id) VALUES (%s, %s)", (user_id, class_id))
            db.commit()
            flash("Registrasi berhasil dan Anda telah terdaftar di kelas.")
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            flash("Username sudah digunakan.")
    return render_template('register.html', classes=classes)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session.pop('selected_class_id', None)
            flash("Login berhasil.")
            return redirect(url_for('dashboard'))
        flash("Username atau password salah.")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Anda sudah logout.")
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Untuk Admin - tampilkan statistik dan sertifikat terbaru
    if g.user.get('role') == 'admin':
        cur.execute("SELECT COUNT(*) as total FROM users WHERE role='student'")
        total_students = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM users WHERE role='sensei'")
        total_teachers = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM materials")
        total_materials = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM quizzes")
        total_quizzes = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM tasks")
        total_tasks = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as total FROM certificates")
        total_certificates = cur.fetchone()['total']
        
        cur.execute("""
            SELECT c.*, u.username, u.full_name, cl.name as class_name
            FROM certificates c
            JOIN users u ON c.student_id = u.id
            LEFT JOIN classes cl ON c.class_id = cl.id
            ORDER BY c.issued_at DESC
            LIMIT 5
        """)
        recent_certificates = cur.fetchall()
        
        return render_template('dashboard.html',
                             total_students=total_students,
                             total_teachers=total_teachers,
                             total_materials=total_materials,
                             total_quizzes=total_quizzes,
                             total_tasks=total_tasks,
                             total_certificates=total_certificates,
                             recent_certificates=recent_certificates)
    
    # Untuk Sensei - tampilkan daftar kelas untuk dipilih
    elif g.user.get('role') == 'sensei':
        cur.execute("SELECT * FROM classes ORDER BY name")
        all_classes = cur.fetchall()
        
        selected_class_id = session.get('selected_class_id')
        selected_class = None
        mats = []
        quizzes = []
        tasks = []
        
        if selected_class_id:
            cur.execute("SELECT * FROM classes WHERE id=%s", (selected_class_id,))
            selected_class = cur.fetchone()
            
            cur.execute("SELECT * FROM materials WHERE class_id=%s ORDER BY created_at DESC", (selected_class_id,))
            mats = cur.fetchall()
            
            cur.execute("SELECT * FROM quizzes WHERE class_id=%s ORDER BY created_at DESC", (selected_class_id,))
            quizzes = cur.fetchall()
            
            cur.execute("SELECT * FROM tasks WHERE class_id=%s ORDER BY created_at DESC", (selected_class_id,))
            tasks = cur.fetchall()
        
        return render_template('dashboard.html', 
                             mats=mats, 
                             quizzes=quizzes, 
                             tasks=tasks,
                             all_classes=all_classes,
                             selected_class=selected_class)
    
    # Untuk Student - tampilkan berdasarkan kelas mereka
    else:
        cur.execute("""
            SELECT class_id FROM enrollments 
            WHERE user_id = %s LIMIT 1
        """, (g.user['id'],))
        enrollment = cur.fetchone()
        
        if enrollment:
            class_id = enrollment['class_id']
            
            cur.execute("SELECT * FROM materials WHERE class_id=%s ORDER BY created_at DESC", (class_id,))
            mats = cur.fetchall()
            
            cur.execute("SELECT * FROM quizzes WHERE class_id=%s ORDER BY created_at DESC", (class_id,))
            quizzes = cur.fetchall()
            
            cur.execute("SELECT * FROM tasks WHERE class_id=%s ORDER BY created_at DESC", (class_id,))
            tasks = cur.fetchall()
        else:
            mats = []
            quizzes = []
            tasks = []
        
        return render_template('dashboard.html', mats=mats, quizzes=quizzes, tasks=tasks)


@app.route('/select_class/<int:class_id>')
@login_required
def select_class(class_id):
    """Route untuk memilih kelas (khusus sensei)"""
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat memilih kelas.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM classes WHERE id=%s", (class_id,))
    class_data = cur.fetchone()
    
    if not class_data:
        flash("Kelas tidak ditemukan.")
        return redirect(url_for('dashboard'))
    
    session['selected_class_id'] = class_id
    flash(f"Kelas '{class_data['name']}' telah dipilih.")
    return redirect(url_for('dashboard'))


@app.route('/clear_class_selection')
@login_required
def clear_class_selection():
    """Route untuk membatalkan pilihan kelas"""
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat membatalkan pilihan kelas.")
        return redirect(url_for('dashboard'))
    
    session.pop('selected_class_id', None)
    flash("Pilihan kelas telah dibatalkan.")
    return redirect(url_for('dashboard'))


@app.route('/classes')
@login_required
def classes():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT c.*, COUNT(e.id) AS total_siswa
        FROM classes c
        LEFT JOIN enrollments e ON e.class_id = c.id
        GROUP BY c.id
    """)
    classes = cur.fetchall()

    cur.execute("""
        SELECT c.* FROM enrollments e
        JOIN classes c ON e.class_id = c.id
        WHERE e.user_id = %s
    """, (g.user['id'],))
    user_class = cur.fetchone()

    return render_template('classes.html', classes=classes, user_class=user_class)


# === ADMIN: ACTIVITY LOGS ===
@app.route('/admin/activities')
@login_required
def admin_activities():
    if g.user.get('role') != 'admin':
        flash("Akses ditolak. Hanya admin yang dapat mengakses halaman ini.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("""
        SELECT u.username, u.full_name, 'Membuat Materi' as activity, m.title as detail, m.created_at as timestamp
        FROM materials m
        JOIN users u ON m.created_by = u.id
        UNION ALL
        SELECT u.username, u.full_name, 'Membuat Kuis', q.title, q.created_at
        FROM quizzes q
        JOIN users u ON q.created_by = u.id
        UNION ALL
        SELECT u.username, u.full_name, 'Membuat Tugas', t.title, t.created_at
        FROM tasks t
        JOIN users u ON t.created_by = u.id
        ORDER BY timestamp DESC
        LIMIT 50
    """)
    teacher_activities = cur.fetchall()
    
    cur.execute("""
        SELECT u.username, u.full_name, 'Mengerjakan Kuis' as activity, 
               CONCAT('Nilai: ', qs.score) as detail, qs.graded_at as timestamp
        FROM quiz_scores qs
        JOIN users u ON qs.student_id = u.id
        UNION ALL
        SELECT u.username, u.full_name, 'Upload Tugas', 
               CONCAT('Tugas ID: ', ts.task_id), ts.submitted_at
        FROM task_submissions ts
        JOIN users u ON ts.student_id = u.id
        ORDER BY timestamp DESC
        LIMIT 50
    """)
    student_activities = cur.fetchall()
    
    return render_template('admin_activities.html', 
                         teacher_activities=teacher_activities,
                         student_activities=student_activities)


@app.route('/admin/users')
@login_required
def admin_users():
    if g.user.get('role') != 'admin':
        flash("Akses ditolak. Hanya admin yang dapat mengakses halaman ini.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("""
        SELECT u.*, 
               COUNT(DISTINCT m.id) as total_materials,
               COUNT(DISTINCT q.id) as total_quizzes,
               COUNT(DISTINCT t.id) as total_tasks
        FROM users u
        LEFT JOIN materials m ON m.created_by = u.id
        LEFT JOIN quizzes q ON q.created_by = u.id
        LEFT JOIN tasks t ON t.created_by = u.id
        WHERE u.role = 'sensei'
        GROUP BY u.id
    """)
    teachers = cur.fetchall()
    
    cur.execute("""
        SELECT u.*, 
               c.name as class_name,
               COUNT(DISTINCT qs.id) as total_quiz_taken,
               ROUND(AVG(qs.score), 2) as avg_score,
               COUNT(DISTINCT ts.id) as total_task_submitted
        FROM users u
        LEFT JOIN enrollments e ON e.user_id = u.id
        LEFT JOIN classes c ON c.id = e.class_id
        LEFT JOIN quiz_scores qs ON qs.student_id = u.id
        LEFT JOIN task_submissions ts ON ts.student_id = u.id
        WHERE u.role = 'student'
        GROUP BY u.id
    """)
    students = cur.fetchall()
    
    return render_template('admin_users.html', teachers=teachers, students=students)


# === ADMIN: CERTIFICATES CRUD ===
@app.route('/admin/certificates')
@login_required
def admin_certificates():
    if g.user.get('role') != 'admin':
        flash("Akses ditolak. Hanya admin yang dapat mengakses halaman ini.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT c.*, u.username, u.full_name, cl.name as class_name
        FROM certificates c
        JOIN users u ON c.student_id = u.id
        LEFT JOIN classes cl ON c.class_id = cl.id
        ORDER BY c.issued_at DESC
    """)
    certificates = cur.fetchall()
    return render_template('admin_certificates.html', certificates=certificates)


@app.route('/admin/certificate/create', methods=['GET', 'POST'])
@login_required
def create_certificate():
    if g.user.get('role') != 'admin':
        flash("Akses ditolak. Hanya admin yang dapat mengakses halaman ini.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        class_id = request.form.get('class_id') or None
        certificate_number = request.form['certificate_number'].strip()
        description = request.form.get('description', '').strip()
        
        cur2 = db.cursor()
        cur2.execute("""
            INSERT INTO certificates (student_id, class_id, certificate_number, description, issued_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, class_id, certificate_number, description, datetime.now()))
        db.commit()
        flash("Sertifikat berhasil dibuat.")
        return redirect(url_for('admin_certificates'))
    
    cur.execute("SELECT id, username, full_name FROM users WHERE role='student' ORDER BY full_name")
    students = cur.fetchall()
    
    cur.execute("SELECT id, name FROM classes ORDER BY name")
    classes = cur.fetchall()
    
    return render_template('create_certificate.html', students=students, classes=classes, edit=False, cert=None)


@app.route('/admin/certificate/<int:cert_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_certificate(cert_id):
    if g.user.get('role') != 'admin':
        flash("Akses ditolak. Hanya admin yang dapat mengakses halaman ini.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM certificates WHERE id=%s", (cert_id,))
    cert = cur.fetchone()
    if not cert:
        flash("Sertifikat tidak ditemukan.")
        return redirect(url_for('admin_certificates'))
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        class_id = request.form.get('class_id') or None
        certificate_number = request.form['certificate_number'].strip()
        description = request.form.get('description', '').strip()
        
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE certificates 
            SET student_id=%s, class_id=%s, certificate_number=%s, description=%s
            WHERE id=%s
        """, (student_id, class_id, certificate_number, description, cert_id))
        db.commit()
        flash("Sertifikat berhasil diperbarui.")
        return redirect(url_for('admin_certificates'))
    
    cur.execute("SELECT id, username, full_name FROM users WHERE role='student' ORDER BY full_name")
    students = cur.fetchall()
    
    cur.execute("SELECT id, name FROM classes ORDER BY name")
    classes = cur.fetchall()
    
    return render_template('create_certificate.html', students=students, classes=classes, edit=True, cert=cert)


@app.route('/admin/certificate/<int:cert_id>/delete')
@login_required
def delete_certificate(cert_id):
    if g.user.get('role') != 'admin':
        flash("Akses ditolak. Hanya admin yang dapat mengakses halaman ini.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM certificates WHERE id=%s", (cert_id,))
    db.commit()
    flash("Sertifikat berhasil dihapus.")
    return redirect(url_for('admin_certificates'))


@app.route('/certificate/<int:cert_id>')
@login_required
def view_certificate(cert_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT c.*, u.username, u.full_name, cl.name as class_name
        FROM certificates c
        JOIN users u ON c.student_id = u.id
        LEFT JOIN classes cl ON c.class_id = cl.id
        WHERE c.id = %s
    """, (cert_id,))
    cert = cur.fetchone()
    
    if not cert:
        flash("Sertifikat tidak ditemukan.")
        return redirect(url_for('dashboard'))
    
    # Pastikan siswa hanya bisa lihat sertifikat mereka sendiri
    if g.user.get('role') == 'student' and cert['student_id'] != g.user['id']:
        flash("Anda tidak memiliki akses ke sertifikat ini.")
        return redirect(url_for('my_certificates'))
    
    return render_template('view_certificate.html', cert=cert)


@app.route('/my-certificates')
@login_required
def my_certificates():
    """Halaman untuk siswa melihat sertifikat mereka"""
    if g.user.get('role') != 'student':
        flash("Halaman ini hanya untuk siswa.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT c.*, cl.name as class_name
        FROM certificates c
        LEFT JOIN classes cl ON c.class_id = cl.id
        WHERE c.student_id = %s
        ORDER BY c.issued_at DESC
    """, (g.user['id'],))
    certificates = cur.fetchall()
    
    return render_template('my_certificates.html', certificates=certificates)


# === MATERI (CRUD) ===
@app.route('/material/create', methods=['GET', 'POST'])
@login_required
@class_required
def create_material():
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat membuat materi.")
        return redirect(url_for('dashboard'))
    
    class_id = session.get('selected_class_id')
    
    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content']
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO materials (title, content, class_id, created_by, created_at) VALUES (%s, %s, %s, %s, %s)",
                    (title, content, class_id, g.user['id'], datetime.now()))
        db.commit()
        flash("Materi berhasil ditambahkan.")
        return redirect(url_for('dashboard'))
    return render_template('create_material.html', edit=False, material=None)


@app.route('/material/<int:mid>')
@login_required
def view_material(mid):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM materials WHERE id=%s", (mid,))
    mat = cur.fetchone()
    if not mat:
        flash("Materi tidak ditemukan.")
        return redirect(url_for('dashboard'))
    return render_template('view_material.html', material=mat)


@app.route('/material/<int:mid>/edit', methods=['GET', 'POST'])
@login_required
def edit_material(mid):
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat mengedit materi.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM materials WHERE id=%s", (mid,))
    material = cur.fetchone()
    if not material:
        flash("Materi tidak ditemukan.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content']
        cur2 = db.cursor()
        cur2.execute("UPDATE materials SET title=%s, content=%s WHERE id=%s", (title, content, mid))
        db.commit()
        flash("Materi berhasil diperbarui.")
        return redirect(url_for('dashboard'))

    return render_template('create_material.html', edit=True, material=material)


@app.route('/material/<int:mid>/delete')
@login_required
def delete_material(mid):
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat menghapus materi.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM materials WHERE id=%s", (mid,))
    db.commit()
    flash("Materi berhasil dihapus.")
    return redirect(url_for('dashboard'))


# === FORUM ===
@app.route('/forum', methods=['GET', 'POST'])
@login_required
def forum():
    db = get_db()
    cur = db.cursor(dictionary=True)
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        cur.execute("INSERT INTO forum_posts (title, body, user_id, created_at) VALUES (%s, %s, %s, %s)",
                    (title, body, g.user['id'], datetime.now()))
        db.commit()
        flash("Postingan forum dibuat.")
        return redirect(url_for('forum'))
    cur.execute("SELECT p.*, u.username FROM forum_posts p LEFT JOIN users u ON u.id=p.user_id ORDER BY p.created_at DESC")
    posts = cur.fetchall()
    return render_template('forum.html', posts=posts)


# === QUIZ (CRUD dasar + pertanyaan) ===
@app.route('/quiz/create', methods=['GET', 'POST'])
@login_required
@class_required
def create_quiz():
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat membuat kuis.")
        return redirect(url_for('dashboard'))
    
    class_id = session.get('selected_class_id')
    
    if request.method == 'POST':
        title = request.form['title'].strip()
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO quizzes (title, class_id, created_by, created_at) VALUES (%s, %s, %s, %s)",
                    (title, class_id, g.user['id'], datetime.now()))
        db.commit()
        flash("Kuis berhasil dibuat.")
        return redirect(url_for('dashboard'))
    return render_template('create_quiz.html', edit=False, quiz=None)


@app.route('/quiz/<int:qid>')
@login_required
def view_quiz(qid):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM quizzes WHERE id=%s", (qid,))
    quiz = cur.fetchone()
    if not quiz:
        flash("Kuis tidak ditemukan.")
        return redirect(url_for('dashboard'))
    
    cur.execute("SELECT * FROM quiz_questions WHERE quiz_id=%s ORDER BY id", (qid,))
    questions = cur.fetchall()
    return render_template('view_quiz.html', quiz=quiz, questions=questions)


@app.route('/quiz/<int:qid>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(qid):
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat mengedit kuis.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM quizzes WHERE id=%s", (qid,))
    quiz = cur.fetchone()
    if not quiz:
        flash("Kuis tidak ditemukan.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        cur2 = db.cursor()
        cur2.execute("UPDATE quizzes SET title=%s WHERE id=%s", (title, qid))
        db.commit()
        flash("Kuis berhasil diperbarui.")
        return redirect(url_for('dashboard'))

    return render_template('create_quiz.html', edit=True, quiz=quiz)


@app.route('/quiz/<int:qid>/delete')
@login_required
def delete_quiz(qid):
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat menghapus kuis.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM quiz_answers WHERE quiz_id=%s", (qid,))
    cur.execute("DELETE FROM quiz_scores WHERE quiz_id=%s", (qid,))
    cur.execute("DELETE FROM quiz_questions WHERE quiz_id=%s", (qid,))
    cur.execute("DELETE FROM quizzes WHERE id=%s", (qid,))
    db.commit()
    flash("Kuis berhasil dihapus.")
    return redirect(url_for('dashboard'))


@app.route('/quiz/<int:qid>/add_question', methods=['GET', 'POST'])
@login_required
def add_question(qid):
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat menambah pertanyaan.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM quizzes WHERE id=%s", (qid,))
    quiz = cur.fetchone()
    if not quiz:
        flash("Kuis tidak ditemukan.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        question = request.form['question'].strip()
        a = request.form['a'].strip()
        b = request.form['b'].strip()
        c = request.form['c'].strip()
        d = request.form['d'].strip()
        correct = request.form['correct'].strip().lower()
        cur.execute("""
            INSERT INTO quiz_questions (quiz_id, question, option_a, option_b, option_c, option_d, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (qid, question, a, b, c, d, correct))
        db.commit()
        flash("Pertanyaan berhasil ditambahkan.")
        return redirect(url_for('add_question', qid=qid))

    cur.execute("SELECT * FROM quiz_questions WHERE quiz_id=%s ORDER BY id", (qid,))
    questions = cur.fetchall()
    return render_template('add_question.html', quiz=quiz, questions=questions)


@app.route('/quiz/<int:qid>/question/<int:qid_q>/edit', methods=['GET', 'POST'])
@login_required
def edit_question(qid, qid_q):
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat mengedit pertanyaan.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM quiz_questions WHERE id=%s AND quiz_id=%s", (qid_q, qid))
    question = cur.fetchone()
    if not question:
        flash("Pertanyaan tidak ditemukan.")
        return redirect(url_for('add_question', qid=qid))

    if request.method == 'POST':
        qtext = request.form['question'].strip()
        a = request.form['a'].strip()
        b = request.form['b'].strip()
        c = request.form['c'].strip()
        d = request.form['d'].strip()
        correct = request.form['correct'].strip().lower()
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE quiz_questions
            SET question=%s, option_a=%s, option_b=%s, option_c=%s, option_d=%s, correct_option=%s
            WHERE id=%s
        """, (qtext, a, b, c, d, correct, qid_q))
        db.commit()
        flash("Pertanyaan berhasil diperbarui.")
        return redirect(url_for('add_question', qid=qid))

    return render_template('edit_question.html', question=question, quiz_id=qid)


@app.route('/quiz/<int:qid>/question/<int:qid_q>/delete')
@login_required
def delete_question(qid, qid_q):
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat menghapus pertanyaan.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM quiz_answers WHERE question_id=%s", (qid_q,))
    cur.execute("DELETE FROM quiz_questions WHERE id=%s AND quiz_id=%s", (qid_q, qid))
    db.commit()
    flash("Pertanyaan berhasil dihapus.")
    return redirect(url_for('add_question', qid=qid))


@app.route('/quiz/<int:qid>/take', methods=['GET', 'POST'])
@login_required
def take_quiz(qid):
    if g.user.get('role') != 'student':
        flash("Akses ditolak. Hanya siswa yang dapat mengerjakan kuis.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM quiz_questions WHERE quiz_id=%s ORDER BY id", (qid,))
    questions = cur.fetchall()
    
    if request.method == 'POST':
        total = len(questions)
        correct_count = 0
        cur_answers = db.cursor()
        for q in questions:
            field = f"q{q['id']}"
            answer = request.form.get(field)
            is_correct = False
            if answer:
                try:
                    if answer.lower() == q['correct_option'].lower():
                        is_correct = True
                except Exception:
                    is_correct = False
            if is_correct:
                correct_count += 1
            cur_answers.execute("""
                INSERT INTO quiz_answers (quiz_id, question_id, student_id, selected_option, is_correct, answered_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (qid, q['id'], g.user['id'], answer, is_correct, datetime.now()))

        score = round((correct_count / total) * 100, 2) if total > 0 else 0
        cur_score = db.cursor()
        cur_score.execute("""
            INSERT INTO quiz_scores (quiz_id, student_id, score, graded_at)
            VALUES (%s, %s, %s, %s)
        """, (qid, g.user['id'], score, datetime.now()))
        db.commit()
        flash("Kuis selesai! Nilai kamu telah dihitung otomatis.")
        return redirect(url_for('quiz_result', qid=qid))

    return render_template('take_quiz.html', questions=questions, quiz_id=qid)


@app.route('/quiz/<int:qid>/result')
@login_required
def quiz_result(qid):
    if g.user.get('role') != 'student':
        flash("Akses ditolak. Hanya siswa yang dapat melihat hasil kuis.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT * FROM quiz_scores
        WHERE quiz_id=%s AND student_id=%s
        ORDER BY graded_at DESC LIMIT 1
    """, (qid, g.user['id']))
    score = cur.fetchone()

    cur.execute("SELECT title FROM quizzes WHERE id=%s", (qid,))
    quiz = cur.fetchone()

    cur.execute("""
        SELECT qq.question, qq.option_a, qq.option_b, qq.option_c, qq.option_d,
               qq.correct_option, qa.selected_option, qa.is_correct
        FROM quiz_questions qq
        LEFT JOIN quiz_answers qa
        ON qq.id = qa.question_id AND qa.student_id = %s
        WHERE qq.quiz_id = %s
        ORDER BY qq.id
    """, (g.user['id'], qid))
    answers = cur.fetchall()

    return render_template('quiz_result.html', quiz=quiz, score=score, answers=answers)


# === TUGAS (CRUD + upload) ===
@app.route('/task/create', methods=['GET', 'POST'])
@login_required
@class_required
def create_task():
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat membuat tugas.")
        return redirect(url_for('dashboard'))
    
    class_id = session.get('selected_class_id')
    
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description']
        due_date = request.form.get('due_date') or None
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO tasks (title, description, due_date, class_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, description, due_date, class_id, g.user['id'], datetime.now()))
        db.commit()
        flash("Tugas berhasil dibuat.")
        return redirect(url_for('dashboard'))
    return render_template('create_task.html', edit=False, task=None)


@app.route('/task/<int:tid>')
@login_required
def view_task(tid):
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM tasks WHERE id=%s", (tid,))
    task = cur.fetchone()
    if not task:
        flash("Tugas tidak ditemukan.")
        return redirect(url_for('dashboard'))
    return render_template('view_task.html', task=task)


@app.route('/task/<int:tid>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(tid):
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat mengedit tugas.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM tasks WHERE id=%s", (tid,))
    task = cur.fetchone()
    if not task:
        flash("Tugas tidak ditemukan.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description']
        due_date = request.form.get('due_date') or None
        cur2 = db.cursor()
        cur2.execute("UPDATE tasks SET title=%s, description=%s, due_date=%s WHERE id=%s",
                     (title, description, due_date, tid))
        db.commit()
        flash("Tugas berhasil diperbarui.")
        return redirect(url_for('dashboard'))

    return render_template('create_task.html', edit=True, task=task)


@app.route('/task/<int:tid>/delete')
@login_required
def delete_task(tid):
    if g.user.get('role') != 'sensei':
        flash("Akses ditolak. Hanya sensei yang dapat menghapus tugas.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM task_submissions WHERE task_id=%s", (tid,))
    cur.execute("DELETE FROM tasks WHERE id=%s", (tid,))
    db.commit()
    flash("Tugas berhasil dihapus.")
    return redirect(url_for('dashboard'))


@app.route('/task/<int:tid>/upload', methods=['GET', 'POST'])
@login_required
def upload_task(tid):
    if g.user.get('role') != 'student':
        flash("Akses ditolak. Hanya siswa yang dapat mengupload tugas.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM tasks WHERE id=%s", (tid,))
    task = cur.fetchone()
    if not task:
        flash("Tugas tidak ditemukan.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            safe_name = f"{g.user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            file.save(filepath)
            cur2 = db.cursor()
            cur2.execute("""
                INSERT INTO task_submissions (task_id, student_id, file_path, submitted_at)
                VALUES (%s, %s, %s, %s)
            """, (tid, g.user['id'], filepath, datetime.now()))
            db.commit()
            flash("Tugas berhasil diupload.")
            return redirect(url_for('dashboard'))
        else:
            flash("Pilih file yang ingin diupload.")
    return render_template('upload_task.html', task=task)


# === PROFILE (VIEW / EDIT / CHANGE PASSWORD) ===
@app.route('/profile')
@login_required
def profile():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, username, full_name, role, bio, avatar FROM users WHERE id=%s", (g.user['id'],))
    user = cur.fetchone()
    if not user:
        flash("Profil tidak ditemukan.")
        return redirect(url_for('dashboard'))
    return render_template('profile.html', user=user)


@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, username, full_name, bio, avatar FROM users WHERE id=%s", (g.user['id'],))
    user = cur.fetchone()
    if not user:
        flash("Profil tidak ditemukan.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip() or None
        bio = request.form.get('bio', '').strip() or None
        file = request.files.get('avatar')
        avatar_filename = user.get('avatar')

        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Format file tidak diizinkan. Gunakan: png, jpg, jpeg, gif.')
                return redirect(url_for('edit_profile'))
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            final_name = f"{g.user['username']}_{timestamp}_{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], final_name)
            file.save(save_path)
            avatar_filename = final_name

        cur2 = db.cursor()
        cur2.execute("UPDATE users SET full_name=%s, bio=%s, avatar=%s WHERE id=%s",
                     (full_name, bio, avatar_filename, g.user['id']))
        db.commit()
        flash('Profil berhasil diperbarui.')
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', user=user)


@app.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current = request.form.get('current_password', '')
        newp = request.form.get('new_password', '')
        newp2 = request.form.get('new_password_confirm', '')

        if not check_password_hash(g.user['password'], current):
            flash('Password saat ini salah.')
            return redirect(url_for('change_password'))
        if not newp or newp != newp2:
            flash('Konfirmasi password tidak cocok atau password baru kosong.')
            return redirect(url_for('change_password'))

        db = get_db()
        cur = db.cursor()
        cur.execute("UPDATE users SET password=%s WHERE id=%s", (generate_password_hash(newp), g.user['id']))
        db.commit()
        flash('Password berhasil diubah. Silakan login ulang jika diperlukan.')
        return redirect(url_for('profile'))

    return render_template('change_password.html')


# === START APP ===
if __name__ == '__main__':
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("INSERT IGNORE INTO users (username,password,role,full_name) VALUES (%s,%s,%s,%s)",
                        ("admin", generate_password_hash("admin123"), "admin", "Administrator"))
            cur.execute("INSERT IGNORE INTO users (username,password,role,full_name) VALUES (%s,%s,%s,%s)",
                        ("sensei", generate_password_hash("sensei123"), "sensei", "Sensei Ichiro"))
            cur.execute("INSERT IGNORE INTO users (username,password,role,full_name) VALUES (%s,%s,%s,%s)",
                        ("siswa", generate_password_hash("siswa123"), "student", "Siswa Aiko"))
            db.commit()
        except Exception as e:
            print("Perhatikan: gagal insert default users (mungkin tabel belum dibuat):", e)
    app.run(debug=True)