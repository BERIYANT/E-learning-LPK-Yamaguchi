from flask import Flask, send_file, render_template, request, redirect, url_for, session, flash, g
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

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'zip', 'rar'}

# === KONFIGURASI DATABASE ===
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'elearning_lpkyamaguchi'
}



# === HELPERS ===
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def normalize_path(file_path):
    """Normalize file path untuk cross-platform compatibility"""
    if file_path:
        # Hapus 'static/' atau 'static\' dari awal path jika ada
        if file_path.startswith('static/') or file_path.startswith('static\\'):
            file_path = file_path.replace('static/', '').replace('static\\', '')
        # Replace backslash dengan forward slash
        return file_path.replace('\\', '/')
    return file_path

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

# === JINJA2 FILTER ===
@app.template_filter('normalize_path')
def normalize_path_filter(file_path):
    """Jinja2 filter untuk normalize file path"""
    return normalize_path(file_path)

    

# === ROUTE UNTUK DOWNLOAD FILE ===
@app.route('/uploads/<path:filename>')
def download_file(filename):
    """Route untuk download atau view uploaded files"""
    try:
        # Normalize path - hapus 'uploads/' jika ada di awal
        if filename.startswith('uploads/'):
            filename = filename[8:]
        
        # Construct full file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Check if file exists
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            flash("File tidak ditemukan.")
            return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f"Error membuka file: {str(e)}")
        return redirect(url_for('dashboard'))

# === ROUTES UTAMA ===
@app.route('/')
def index():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM materials ORDER BY created_at DESC")
    materials = cur.fetchall()
    return render_template('index.html', materials=materials)


# HAPUS route /register yang lama dan ganti dengan ini:

@app.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    """Admin mendaftarkan user baru (siswa atau guru)"""
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
            flash(f"User {username} berhasil didaftarkan sebagai {role}.")
            return redirect(url_for('admin_users'))
        except mysql.connector.IntegrityError:
            flash("Username sudah digunakan.")
    return render_template('register.html', classes=classes)

# TAMBAHKAN route ini ke app.py setelah route admin_users

@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """Admin mengedit data user"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Ambil data user
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    
    if not user:
        flash("User tidak ditemukan.")
        return redirect(url_for('admin_users'))
    
    # Cegah admin mengedit dirinya sendiri
    if user_id == g.user['id']:
        flash("Anda tidak dapat mengedit data Anda sendiri dari halaman ini. Gunakan menu Profile.")
        return redirect(url_for('admin_users'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'student')
        new_password = request.form.get('new_password', '').strip()
        class_id = request.form.get('class_id')
        
        # Validasi username unique (kecuali username sendiri)
        cur.execute("SELECT id FROM users WHERE username=%s AND id!=%s", (username, user_id))
        if cur.fetchone():
            flash("Username sudah digunakan oleh user lain.")
            # Ambil data kelas untuk form
            cur.execute("SELECT * FROM classes ORDER BY name")
            classes = cur.fetchall()
            cur.execute("SELECT class_id FROM enrollments WHERE user_id=%s LIMIT 1", (user_id,))
            current_enrollment = cur.fetchone()
            return render_template('admin_edit_user.html', user=user, classes=classes, 
                                 current_enrollment=current_enrollment)
        
        cur2 = db.cursor()
        
        # Update data user
        if new_password:
            # Jika ada password baru, update dengan password baru
            hashed_password = generate_password_hash(new_password)
            cur2.execute("""
                UPDATE users 
                SET username=%s, full_name=%s, role=%s, password=%s
                WHERE id=%s
            """, (username, full_name, role, hashed_password, user_id))
        else:
            # Jika tidak ada password baru, update tanpa mengubah password
            cur2.execute("""
                UPDATE users 
                SET username=%s, full_name=%s, role=%s
                WHERE id=%s
            """, (username, full_name, role, user_id))
        
        # Update enrollment untuk student
        if role == 'student':
            # Hapus enrollment lama
            cur2.execute("DELETE FROM enrollments WHERE user_id=%s", (user_id,))
            # Tambah enrollment baru jika ada class_id
            if class_id:
                cur2.execute("INSERT INTO enrollments (user_id, class_id) VALUES (%s, %s)", 
                           (user_id, class_id))
        else:
            # Jika bukan student, hapus semua enrollment
            cur2.execute("DELETE FROM enrollments WHERE user_id=%s", (user_id,))
        
        db.commit()
        flash(f"Data user {username} berhasil diperbarui.")
        return redirect(url_for('admin_users'))
    
    # Ambil data kelas untuk dropdown
    cur.execute("SELECT * FROM classes ORDER BY name")
    classes = cur.fetchall()
    
    # Ambil enrollment user saat ini
    cur.execute("SELECT class_id FROM enrollments WHERE user_id=%s LIMIT 1", (user_id,))
    current_enrollment = cur.fetchone()
    
    return render_template('admin_edit_user.html', user=user, classes=classes, 
                         current_enrollment=current_enrollment)


@app.route('/admin/user/<int:user_id>/delete')
@login_required
@admin_required
def admin_delete_user(user_id):
    """Admin menghapus user"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Cek apakah user ada
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    
    if not user:
        flash("User tidak ditemukan.")
        return redirect(url_for('admin_users'))
    
    # Cegah admin menghapus dirinya sendiri
    if user_id == g.user['id']:
        flash("Anda tidak dapat menghapus akun Anda sendiri.")
        return redirect(url_for('admin_users'))
    
    cur2 = db.cursor()
    
    # Hapus semua data terkait user
    # 1. Enrollments
    cur2.execute("DELETE FROM enrollments WHERE user_id=%s", (user_id,))
    
    # 2. Quiz answers dan scores
    cur2.execute("DELETE FROM quiz_answers WHERE student_id=%s", (user_id,))
    cur2.execute("DELETE FROM quiz_scores WHERE student_id=%s", (user_id,))
    
    # 3. Task submissions
    cur2.execute("DELETE FROM task_submissions WHERE student_id=%s", (user_id,))
    
    # 4. Forum posts dan replies
    cur2.execute("DELETE FROM forum_replies WHERE user_id=%s", (user_id,))
    cur2.execute("DELETE FROM forum_posts WHERE user_id=%s", (user_id,))
    
    # 5. Certificates
    cur2.execute("DELETE FROM certificates WHERE student_id=%s", (user_id,))
    
    # 6. Materials, quizzes, tasks yang dibuat (jika sensei)
    if user['role'] == 'sensei':
        # Hapus materials
        cur2.execute("DELETE FROM materials WHERE created_by=%s", (user_id,))
        
        # Hapus quizzes beserta questions, answers, dan scores
        cur2.execute("SELECT id FROM quizzes WHERE created_by=%s", (user_id,))
        quiz_ids = cur2.fetchall()
        for quiz in quiz_ids:
            qid = quiz[0]
            cur2.execute("DELETE FROM quiz_answers WHERE quiz_id=%s", (qid,))
            cur2.execute("DELETE FROM quiz_scores WHERE quiz_id=%s", (qid,))
            cur2.execute("DELETE FROM quiz_questions WHERE quiz_id=%s", (qid,))
        cur2.execute("DELETE FROM quizzes WHERE created_by=%s", (user_id,))
        
        # Hapus tasks beserta submissions
        cur2.execute("DELETE FROM task_submissions WHERE task_id IN (SELECT id FROM tasks WHERE created_by=%s)", (user_id,))
        cur2.execute("DELETE FROM tasks WHERE created_by=%s", (user_id,))
    
    # 7. Hapus user
    cur2.execute("DELETE FROM users WHERE id=%s", (user_id,))
    
    db.commit()
    
    flash(f"User {user['username']} dan semua data terkait berhasil dihapus.")
    return redirect(url_for('admin_users'))


@app.route('/admin/user/<int:user_id>/reset-password', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    """Admin mereset password user"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()
    
    if not user:
        flash("User tidak ditemukan.")
        return redirect(url_for('admin_users'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            flash("Password tidak boleh kosong.")
            return render_template('admin_reset_password.html', user=user)
        
        if new_password != confirm_password:
            flash("Konfirmasi password tidak cocok.")
            return render_template('admin_reset_password.html', user=user)
        
        if len(new_password) < 6:
            flash("Password minimal 6 karakter.")
            return render_template('admin_reset_password.html', user=user)
        
        cur2 = db.cursor()
        hashed_password = generate_password_hash(new_password)
        cur2.execute("UPDATE users SET password=%s WHERE id=%s", (hashed_password, user_id))
        db.commit()
        
        flash(f"Password user {user['username']} berhasil direset.")
        return redirect(url_for('admin_users'))
    
    return render_template('admin_reset_password.html', user=user)

# TAMBAHKAN route baru untuk admin melihat halaman register dari admin panel
@app.route('/admin/register')
@login_required
@admin_required
def admin_register():
    """Redirect ke halaman register (yang sekarang hanya bisa diakses admin)"""
    return redirect(url_for('register'))

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
    
    # Untuk Student - tampilkan berdasarkan kelas mereka dengan status pengerjaan
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
            
            # Ambil kuis dengan status pengerjaan
            cur.execute("""
                SELECT q.*,
                    (SELECT COUNT(*) FROM quiz_scores WHERE quiz_id = q.id AND student_id = %s) as is_completed
                FROM quizzes q
                WHERE q.class_id = %s
                ORDER BY q.created_at DESC
            """, (g.user['id'], class_id))
            quizzes = cur.fetchall()
            
            # Ambil tugas dengan status pengerjaan dan nilai
            cur.execute("""
                SELECT t.*,
                    ts.id as submission_id,
                    ts.score,
                    ts.submitted_at,
                    ts.graded_at
                FROM tasks t
                LEFT JOIN task_submissions ts ON t.id = ts.task_id AND ts.student_id = %s
                WHERE t.class_id = %s
                ORDER BY t.created_at DESC
            """, (g.user['id'], class_id))
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


# === ADMIN: KELOLA KELAS ===
@app.route('/admin/classes')
@login_required
@admin_required
def admin_classes():
    """Halaman admin untuk melihat semua kelas"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT c.*, COUNT(e.id) AS total_students
        FROM classes c
        LEFT JOIN enrollments e ON e.class_id = c.id
        GROUP BY c.id
        ORDER BY c.name
    """)
    classes = cur.fetchall()
    return render_template('admin_classes.html', classes=classes)


@app.route('/admin/class/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_class():
    """Admin membuat kelas baru"""
    if request.method == 'POST':
        name = request.form['name'].strip()
        schedule = request.form.get('schedule', '').strip()
        description = request.form.get('description', '').strip()
        
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO classes (name, schedule, description, created_at)
            VALUES (%s, %s, %s, %s)
        """, (name, schedule, description, datetime.now()))
        db.commit()
        flash("Kelas berhasil ditambahkan.")
        return redirect(url_for('admin_classes'))
    
    return render_template('admin_create_class.html')


@app.route('/admin/class/<int:class_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_class(class_id):
    """Admin mengedit kelas"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM classes WHERE id=%s", (class_id,))
    class_data = cur.fetchone()
    
    if not class_data:
        flash("Kelas tidak ditemukan.")
        return redirect(url_for('admin_classes'))
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        schedule = request.form.get('schedule', '').strip()
        description = request.form.get('description', '').strip()
        
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE classes 
            SET name=%s, schedule=%s, description=%s
            WHERE id=%s
        """, (name, schedule, description, class_id))
        db.commit()
        flash("Kelas berhasil diperbarui.")
        return redirect(url_for('admin_classes'))
    
    return render_template('admin_edit_class.html', class_data=class_data)


@app.route('/admin/class/<int:class_id>/delete')
@login_required
@admin_required
def admin_delete_class(class_id):
    """Admin menghapus kelas"""
    db = get_db()
    cur = db.cursor()
    
    # Hapus data terkait terlebih dahulu
    cur.execute("DELETE FROM enrollments WHERE class_id=%s", (class_id,))
    cur.execute("DELETE FROM materials WHERE class_id=%s", (class_id,))
    cur.execute("DELETE FROM quizzes WHERE class_id=%s", (class_id,))
    cur.execute("DELETE FROM tasks WHERE class_id=%s", (class_id,))
    cur.execute("UPDATE certificates SET class_id=NULL WHERE class_id=%s", (class_id,))
    cur.execute("DELETE FROM classes WHERE id=%s", (class_id,))
    
    db.commit()
    flash("Kelas berhasil dihapus beserta semua data terkait.")
    return redirect(url_for('admin_classes'))


# === ADMIN: ACTIVITY LOGS ===
@app.route('/admin/activities')
@login_required
@admin_required
def admin_activities():
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
@admin_required
def admin_users():
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
@admin_required
def admin_certificates():
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

# Route create_certificate - HAPUS bagian class_id
@app.route('/admin/certificate/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_certificate():
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        certificate_number = request.form['certificate_number'].strip()
        description = request.form.get('description', '').strip()
        file_path = None
        
        # Validasi student_id
        if not student_id:
            flash('Pilih siswa terlebih dahulu.')
            cur.execute("SELECT id, username, full_name FROM users WHERE role='student' ORDER BY full_name")
            students = cur.fetchall()
            return render_template('create_certificate.html', students=students, edit=False, cert=None)
        
        # Handle file upload
        file = request.files.get('file')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Format file tidak diizinkan. Gunakan PDF, JPG, PNG, GIF, DOC, atau DOCX.')
                cur.execute("SELECT id, username, full_name FROM users WHERE role='student' ORDER BY full_name")
                students = cur.fetchall()
                return render_template('create_certificate.html', students=students, edit=False, cert=None)
            
            # Generate safe filename
            safe_name = f"cert_{certificate_number.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            
            try:
                file.save(filepath)
                # ⬇️ PERBAIKAN: Simpan hanya nama file, BUKAN dengan prefix "uploads/"
                file_path = safe_name
            except Exception as e:
                flash(f'Gagal mengupload file: {str(e)}')
                cur.execute("SELECT id, username, full_name FROM users WHERE role='student' ORDER BY full_name")
                students = cur.fetchall()
                return render_template('create_certificate.html', students=students, edit=False, cert=None)
        
        # Insert to database - TANPA class_id
        cur2 = db.cursor()
        try:
            cur2.execute("""
                INSERT INTO certificates (student_id, certificate_number, description, file_path, issued_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (student_id, certificate_number, description, file_path, datetime.now()))
            db.commit()
            flash("Sertifikat berhasil dibuat.")
            return redirect(url_for('admin_certificates'))
        except mysql.connector.IntegrityError as e:
            flash(f'Error: Nomor sertifikat mungkin sudah digunakan. {str(e)}')
            # Hapus file jika insert gagal
            if file_path:
                try:
                    os.remove(filepath)
                except:
                    pass
    
    # GET request - tampilkan form (TANPA classes)
    cur.execute("SELECT id, username, full_name FROM users WHERE role='student' ORDER BY full_name")
    students = cur.fetchall()
    
    return render_template('create_certificate.html', students=students, edit=False, cert=None)
# Route edit_certificate - HAPUS bagian class_id
@app.route('/admin/certificate/<int:cert_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_certificate(cert_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM certificates WHERE id=%s", (cert_id,))
    cert = cur.fetchone()
    if not cert:
        flash("Sertifikat tidak ditemukan.")
        return redirect(url_for('admin_certificates'))
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        certificate_number = request.form['certificate_number'].strip()
        description = request.form.get('description', '').strip()
        file_path = cert.get('file_path')
        
        # Validasi student_id
        if not student_id:
            flash('Pilih siswa terlebih dahulu.')
            cur.execute("SELECT id, username, full_name FROM users WHERE role='student' ORDER BY full_name")
            students = cur.fetchall()
            return render_template('create_certificate.html', students=students, edit=True, cert=cert)
        
        # Handle file upload baru
        file = request.files.get('file')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Format file tidak diizinkan. Gunakan PDF, JPG, PNG, GIF, DOC, atau DOCX.')
                cur.execute("SELECT id, username, full_name FROM users WHERE role='student' ORDER BY full_name")
                students = cur.fetchall()
                return render_template('create_certificate.html', students=students, edit=True, cert=cert)
            
            # ⬇️ PERBAIKAN: Hapus file lama dengan mencoba berbagai path
            if file_path:
                old_paths = [
                    os.path.join(app.config['UPLOAD_FOLDER'], file_path),
                    os.path.join(app.config['UPLOAD_FOLDER'], file_path.replace('uploads/', '')),
                    os.path.join('static', file_path),
                    os.path.join('static', 'uploads', file_path.replace('uploads/', ''))
                ]
                for old_file in old_paths:
                    if os.path.exists(old_file):
                        try:
                            os.remove(old_file)
                            print(f"File lama berhasil dihapus: {old_file}")
                            break
                        except Exception as e:
                            print(f"Gagal menghapus file lama: {e}")
            
            # Upload file baru
            safe_name = f"cert_{certificate_number.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            
            try:
                file.save(filepath)
                # ⬇️ PERBAIKAN: Simpan hanya nama file, BUKAN dengan prefix "uploads/"
                file_path = safe_name
            except Exception as e:
                flash(f'Gagal mengupload file: {str(e)}')
                cur.execute("SELECT id, username, full_name FROM users WHERE role='student' ORDER BY full_name")
                students = cur.fetchall()
                return render_template('create_certificate.html', students=students, edit=True, cert=cert)
        
        # Opsi hapus file
        if request.form.get('remove_file') == 'yes' and file_path:
            # ⬇️ PERBAIKAN: Coba berbagai path saat menghapus
            old_paths = [
                os.path.join(app.config['UPLOAD_FOLDER'], file_path),
                os.path.join(app.config['UPLOAD_FOLDER'], file_path.replace('uploads/', '')),
                os.path.join('static', file_path),
                os.path.join('static', 'uploads', file_path.replace('uploads/', ''))
            ]
            for old_file in old_paths:
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                        print(f"File berhasil dihapus: {old_file}")
                        break
                    except Exception as e:
                        print(f"Gagal menghapus file: {e}")
            file_path = None
        
        # Update database - TANPA class_id
        cur2 = db.cursor()
        try:
            cur2.execute("""
                UPDATE certificates 
                SET student_id=%s, certificate_number=%s, description=%s, file_path=%s
                WHERE id=%s
            """, (student_id, certificate_number, description, file_path, cert_id))
            db.commit()
            flash("Sertifikat berhasil diperbarui.")
            return redirect(url_for('admin_certificates'))
        except mysql.connector.IntegrityError as e:
            flash(f'Error: Nomor sertifikat mungkin sudah digunakan. {str(e)}')
    
    # GET request - tampilkan form (TANPA classes)
    cur.execute("SELECT id, username, full_name FROM users WHERE role='student' ORDER BY full_name")
    students = cur.fetchall()
    
    return render_template('create_certificate.html', students=students, edit=True, cert=cert)

@app.route('/admin/certificate/<int:cert_id>/delete')
@login_required
@admin_required
def delete_certificate(cert_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Ambil data sertifikat untuk mendapatkan file_path
    cur.execute("SELECT file_path FROM certificates WHERE id=%s", (cert_id,))
    cert = cur.fetchone()
    
    if cert and cert.get('file_path'):
        # ⬇️ PERBAIKAN: Hapus file fisik - coba berbagai kemungkinan path
        file_path = cert['file_path']
        possible_paths = [
            os.path.join(app.config['UPLOAD_FOLDER'], file_path),
            os.path.join(app.config['UPLOAD_FOLDER'], file_path.replace('uploads/', '')),
            os.path.join('static', file_path),
            os.path.join('static', 'uploads', file_path.replace('uploads/', ''))
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"File berhasil dihapus: {path}")
                    break
                except Exception as e:
                    print(f"Gagal menghapus file di {path}: {e}")
    
    # Hapus record dari database
    cur2 = db.cursor()
    cur2.execute("DELETE FROM certificates WHERE id=%s", (cert_id,))
    db.commit()
    
    flash("Sertifikat berhasil dihapus.")
    return redirect(url_for('admin_certificates'))

# === DOWNLOAD SERTIFIKAT (KHUSUS) ===
@app.route('/certificate/<int:cert_id>/download')
@login_required
def download_certificate_file(cert_id):
    """Route untuk DOWNLOAD file sertifikat dengan security check"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM certificates WHERE id=%s", (cert_id,))
    cert = cur.fetchone()
    
    if not cert:
        flash("Sertifikat tidak ditemukan.")
        return redirect(url_for('dashboard'))
    
    # Security: siswa hanya bisa download sertifikat mereka sendiri
    if g.user.get('role') == 'student' and cert['student_id'] != g.user['id']:
        flash("Anda tidak memiliki akses ke sertifikat ini.")
        return redirect(url_for('my_certificates'))
    
    if not cert.get('file_path'):
        flash("Sertifikat ini tidak memiliki file.")
        return redirect(url_for('my_certificates'))
    
    try:
        # Normalize path - hapus 'uploads/' jika ada
        file_path = cert['file_path']
        if file_path.startswith('uploads/'):
            file_path = file_path[8:]
        
        # Coba cari file di berbagai lokasi
        possible_paths = [
            os.path.join(app.config['UPLOAD_FOLDER'], file_path),  # static/uploads/filename
            os.path.join('static', 'uploads', file_path),           # static/uploads/filename
        ]
        
        actual_path = None
        for path in possible_paths:
            if os.path.exists(path):
                actual_path = path
                break
        
        if actual_path:
            # Tentukan nama file download
            file_ext = file_path.split('.')[-1] if '.' in file_path else 'pdf'
            download_name = f"Sertifikat_{cert['certificate_number'].replace(' ', '_')}.{file_ext}"
            
            return send_file(
                actual_path,
                as_attachment=True,
                download_name=download_name
            )
        else:
            flash("File sertifikat tidak ditemukan di server. Silakan hubungi admin.")
            return redirect(url_for('my_certificates'))
        
    except Exception as e:
        flash(f"Error saat mengunduh file: {str(e)}")
        return redirect(url_for('my_certificates'))
    
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
        file_path = None
        
        # Handle file upload
        file = request.files.get('file')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Format file tidak diizinkan.')
                return redirect(url_for('create_material'))
            
            safe_name = f"material_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            file.save(filepath)
            file_path = f"uploads/{safe_name}"
        
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO materials (title, content, file_path, class_id, created_by, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, content, file_path, class_id, g.user['id'], datetime.now()))
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


# Ganti route edit_material yang lama dengan ini:
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
        file_path = material.get('file_path')
        
        # Handle file upload
        file = request.files.get('file')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Format file tidak diizinkan.')
                return redirect(url_for('edit_material', mid=mid))
            
            # Hapus file lama jika ada
            if file_path:
                old_file = os.path.join('static', file_path)
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                    except:
                        pass
            
            # Upload file baru
            safe_name = f"material_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            file.save(filepath)
            file_path = f"uploads/{safe_name}"
        
        # Opsi hapus file
        if request.form.get('remove_file') == 'yes' and file_path:
            old_file = os.path.join('static', file_path)
            if os.path.exists(old_file):
                try:
                    os.remove(old_file)
                except:
                    pass
            file_path = None
        
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE materials 
            SET title=%s, content=%s, file_path=%s 
            WHERE id=%s
        """, (title, content, file_path, mid))
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
    
    # Ambil data kuis dengan jumlah pertanyaan
    cur.execute("""
        SELECT q.*, COUNT(qq.id) as total_questions
        FROM quizzes q
        LEFT JOIN quiz_questions qq ON qq.quiz_id = q.id
        WHERE q.id = %s
        GROUP BY q.id
    """, (qid,))
    quiz = cur.fetchone()
    
    if not quiz:
        flash("Kuis tidak ditemukan.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        
        if not title:
            flash("Judul kuis tidak boleh kosong.")
            return render_template('edit_quiz.html', quiz=quiz)
        
        cur2 = db.cursor()
        cur2.execute("UPDATE quizzes SET title=%s WHERE id=%s", (title, qid))
        db.commit()
        flash("Kuis berhasil diperbarui.")
        return redirect(url_for('dashboard'))

    return render_template('edit_quiz.html', quiz=quiz)

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


# Update route add_question untuk 5 opsi
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
        e = request.form['e'].strip()  # TAMBAHAN OPSI E
        correct = request.form['correct'].strip().lower()
        
        # Validasi jawaban benar
        if correct not in ['a', 'b', 'c', 'd', 'e']:
            flash("Jawaban benar harus salah satu dari A, B, C, D, atau E.")
            return redirect(url_for('add_question', qid=qid))
        
        cur.execute("""
            INSERT INTO quiz_questions (quiz_id, question, option_a, option_b, option_c, option_d, option_e, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (qid, question, a, b, c, d, e, correct))
        db.commit()
        flash("Pertanyaan berhasil ditambahkan.")
        return redirect(url_for('add_question', qid=qid))

    cur.execute("SELECT * FROM quiz_questions WHERE quiz_id=%s ORDER BY id", (qid,))
    questions = cur.fetchall()
    return render_template('add_question.html', quiz=quiz, questions=questions)


# Update route edit_question untuk 5 opsi
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
        e = request.form['e'].strip()  # TAMBAHAN OPSI E
        correct = request.form['correct'].strip().lower()
        
        # Validasi jawaban benar
        if correct not in ['a', 'b', 'c', 'd', 'e']:
            flash("Jawaban benar harus salah satu dari A, B, C, D, atau E.")
            return render_template('edit_question.html', question=question, quiz_id=qid)
        
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE quiz_questions
            SET question=%s, option_a=%s, option_b=%s, option_c=%s, option_d=%s, option_e=%s, correct_option=%s
            WHERE id=%s
        """, (qtext, a, b, c, d, e, correct, qid_q))
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


# GANTI route create_task yang lama dengan ini:

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
        file_path = None
        
        # Handle file upload untuk tugas dari guru
        file = request.files.get('file')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Format file tidak diizinkan.')
                return redirect(url_for('create_task'))
            
            safe_name = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            file.save(filepath)
            # Simpan hanya nama file tanpa prefix "uploads/"
            file_path = safe_name
        
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO tasks (title, description, due_date, file_path, class_id, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (title, description, due_date, file_path, class_id, g.user['id'], datetime.now()))
        db.commit()
        flash("Tugas berhasil dibuat.")
        return redirect(url_for('dashboard'))
    return render_template('create_task.html', edit=False, task=None)


# GANTI route view_task yang lama dengan ini:

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
    
    # Cek apakah siswa sudah submit tugas ini
    submission = None
    if g.user.get('role') == 'student':
        cur.execute("""
            SELECT * FROM task_submissions 
            WHERE task_id=%s AND student_id=%s 
            ORDER BY submitted_at DESC LIMIT 1
        """, (tid, g.user['id']))
        submission = cur.fetchone()
    
    return render_template('view_task.html', task=task, submission=submission)


# GANTI route edit_task yang lama dengan ini:

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
        file_path = task.get('file_path')
        
        # Handle file upload baru
        file = request.files.get('file')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Format file tidak diizinkan.')
                return redirect(url_for('edit_task', tid=tid))
            
            # Hapus file lama jika ada
            if file_path:
                old_paths = [
                    os.path.join(app.config['UPLOAD_FOLDER'], file_path),
                    os.path.join(app.config['UPLOAD_FOLDER'], file_path.replace('uploads/', '')),
                    os.path.join('static', file_path),
                    os.path.join('static', 'uploads', file_path.replace('uploads/', ''))
                ]
                for old_file in old_paths:
                    if os.path.exists(old_file):
                        try:
                            os.remove(old_file)
                            break
                        except Exception as e:
                            print(f"Gagal menghapus file lama: {e}")
            
            # Upload file baru
            safe_name = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            file.save(filepath)
            file_path = safe_name
        
        # Opsi hapus file
        if request.form.get('remove_file') == 'yes' and file_path:
            old_paths = [
                os.path.join(app.config['UPLOAD_FOLDER'], file_path),
                os.path.join(app.config['UPLOAD_FOLDER'], file_path.replace('uploads/', '')),
                os.path.join('static', file_path),
                os.path.join('static', 'uploads', file_path.replace('uploads/', ''))
            ]
            for old_file in old_paths:
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                        break
                    except Exception as e:
                        print(f"Gagal menghapus file: {e}")
            file_path = None
        
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE tasks 
            SET title=%s, description=%s, due_date=%s, file_path=%s 
            WHERE id=%s
        """, (title, description, due_date, file_path, tid))
        db.commit()
        flash("Tugas berhasil diperbarui.")
        return redirect(url_for('dashboard'))

    return render_template('create_task.html', edit=True, task=task)


# TAMBAHKAN route baru untuk download file tugas

@app.route('/task/<int:tid>/download')
@login_required
def download_task_file(tid):
    """Route untuk download file tugas yang diupload guru"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT file_path, title FROM tasks WHERE id=%s", (tid,))
    task = cur.fetchone()
    
    if not task:
        flash("Tugas tidak ditemukan.")
        return redirect(url_for('dashboard'))
    
    if not task.get('file_path'):
        flash("Tugas ini tidak memiliki file.")
        return redirect(url_for('view_task', tid=tid))
    
    try:
        # Normalize path
        file_path = task['file_path']
        if file_path.startswith('uploads/'):
            file_path = file_path[8:]
        
        # Cari file di berbagai lokasi
        possible_paths = [
            os.path.join(app.config['UPLOAD_FOLDER'], file_path),
            os.path.join('static', 'uploads', file_path),
            os.path.join('static', task['file_path'])
        ]
        
        for full_path in possible_paths:
            if os.path.exists(full_path):
                # Dapatkan ekstensi file
                file_ext = file_path.split('.')[-1] if '.' in file_path else 'file'
                download_name = f"{task['title']}.{file_ext}"
                
                return send_file(
                    full_path,
                    as_attachment=True,
                    download_name=download_name
                )
        
        # Jika file tidak ditemukan
        flash(f"File tidak ditemukan di server.")
        return redirect(url_for('view_task', tid=tid))
        
    except Exception as e:
        flash(f"Error: {str(e)}")
        return redirect(url_for('view_task', tid=tid))

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
    
    # Cek apakah sudah ada submission sebelumnya
    cur.execute("""
        SELECT * FROM task_submissions 
        WHERE task_id=%s AND student_id=%s 
        ORDER BY submitted_at DESC LIMIT 1
    """, (tid, g.user['id']))
    existing_submission = cur.fetchone()

    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Format file tidak diizinkan.')
                return redirect(url_for('upload_task', tid=tid))
                
            safe_name = f"{g.user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            file.save(filepath)
            
            # Simpan dengan format uploads/filename
            db_filepath = f"uploads/{safe_name}"
            
            cur2 = db.cursor()
            
            # Jika sudah ada submission, UPDATE (bukan INSERT baru)
            if existing_submission:
                # Hapus file lama jika ada
                if existing_submission.get('file_path'):
                    old_file_path = existing_submission['file_path']
                    old_paths = [
                        os.path.join(app.config['UPLOAD_FOLDER'], old_file_path.replace('uploads/', '')),
                        os.path.join('static', old_file_path),
                        os.path.join('static', 'uploads', old_file_path.replace('uploads/', ''))
                    ]
                    for old_file in old_paths:
                        if os.path.exists(old_file):
                            try:
                                os.remove(old_file)
                                break
                            except Exception as e:
                                print(f"Gagal menghapus file lama: {e}")
                
                # Update submission yang sudah ada dan reset nilai
                cur2.execute("""
                    UPDATE task_submissions 
                    SET file_path=%s, submitted_at=%s, score=NULL, feedback=NULL, graded_by=NULL, graded_at=NULL
                    WHERE id=%s
                """, (db_filepath, datetime.now(), existing_submission['id']))
                flash("File tugas berhasil diperbarui. Nilai sebelumnya telah dihapus.")
            else:
                # Insert submission baru
                cur2.execute("""
                    INSERT INTO task_submissions (task_id, student_id, file_path, submitted_at)
                    VALUES (%s, %s, %s, %s)
                """, (tid, g.user['id'], db_filepath, datetime.now()))
                flash("Tugas berhasil diupload.")
            
            db.commit()
            return redirect(url_for('my_task_scores'))
        else:
            flash("Pilih file yang ingin diupload.")
    
    return render_template('upload_task.html', task=task, existing_submission=existing_submission)

@app.route('/task/submission/<int:submission_id>/delete')
@login_required
def delete_task_submission(submission_id):
    """Siswa menghapus submission tugas mereka sendiri"""
    if g.user.get('role') != 'student':
        flash("Akses ditolak.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Ambil data submission
    cur.execute("""
        SELECT * FROM task_submissions 
        WHERE id=%s AND student_id=%s
    """, (submission_id, g.user['id']))
    submission = cur.fetchone()
    
    if not submission:
        flash("Submission tidak ditemukan atau Anda tidak memiliki akses.")
        return redirect(url_for('my_task_scores'))
    
    # Hapus file fisik
    if submission.get('file_path'):
        file_path = submission['file_path']
        possible_paths = [
            os.path.join(app.config['UPLOAD_FOLDER'], file_path.replace('uploads/', '')),
            os.path.join('static', file_path),
            os.path.join('static', 'uploads', file_path.replace('uploads/', ''))
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"File berhasil dihapus: {path}")
                    break
                except Exception as e:
                    print(f"Gagal menghapus file: {e}")
    
    # Hapus record dari database
    cur2 = db.cursor()
    cur2.execute("DELETE FROM task_submissions WHERE id=%s", (submission_id,))
    db.commit()
    
    flash("File tugas berhasil dihapus.")
    return redirect(url_for('upload_task', tid=submission['task_id']))

# === GURU: LIHAT & NILAI TUGAS SISWA ===
@app.route('/task/<int:tid>/submissions')
@login_required
def view_task_submissions(tid):
    """Guru melihat semua submission tugas dari siswa"""
    if g.user.get('role') not in ['sensei', 'admin']:
        flash("Akses ditolak. Hanya guru yang dapat melihat submission tugas.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Ambil data tugas
    cur.execute("SELECT * FROM tasks WHERE id=%s", (tid,))
    task = cur.fetchone()
    
    if not task:
        flash("Tugas tidak ditemukan.")
        return redirect(url_for('dashboard'))
    
    # Ambil semua submission
    cur.execute("""
        SELECT ts.*, u.username, u.full_name
        FROM task_submissions ts
        JOIN users u ON ts.student_id = u.id
        WHERE ts.task_id = %s
        ORDER BY ts.submitted_at DESC
    """, (tid,))
    submissions = cur.fetchall()
    
    return render_template('view_task_submissions.html', task=task, submissions=submissions)


@app.route('/task/submission/<int:submission_id>/grade', methods=['GET', 'POST'])
@login_required
def grade_task_submission(submission_id):
    """Guru memberikan nilai pada submission tugas siswa"""
    if g.user.get('role') not in ['sensei', 'admin']:
        flash("Akses ditolak. Hanya guru yang dapat memberikan nilai.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("""
        SELECT ts.*, u.username, u.full_name, t.title as task_title
        FROM task_submissions ts
        JOIN users u ON ts.student_id = u.id
        JOIN tasks t ON ts.task_id = t.id
        WHERE ts.id = %s
    """, (submission_id,))
    submission = cur.fetchone()
    
    if not submission:
        flash("Submission tidak ditemukan.")
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        score = request.form.get('score', '').strip()
        feedback = request.form.get('feedback', '').strip()
        
        # Validasi score
        try:
            score = float(score)
            if score < 0 or score > 100:
                flash("Nilai harus antara 0-100.")
                return redirect(url_for('grade_task_submission', submission_id=submission_id))
        except ValueError:
            flash("Nilai harus berupa angka.")
            return redirect(url_for('grade_task_submission', submission_id=submission_id))
        
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE task_submissions 
            SET score=%s, feedback=%s, graded_by=%s, graded_at=%s
            WHERE id=%s
        """, (score, feedback, g.user['id'], datetime.now(), submission_id))
        db.commit()
        
        flash("Nilai berhasil diberikan.")
        return redirect(url_for('view_task_submissions', tid=submission['task_id']))
    
    return render_template('grade_task_submission.html', submission=submission)


# === SISWA: LIHAT NILAI TUGAS ===
@app.route('/my-task-scores')
@login_required
def my_task_scores():
    """Siswa melihat semua nilai tugas mereka"""
    if g.user.get('role') != 'student':
        flash("Halaman ini hanya untuk siswa.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("""
        SELECT ts.*, t.title as task_title, t.due_date,
               u.full_name as graded_by_name
        FROM task_submissions ts
        JOIN tasks t ON ts.task_id = t.id
        LEFT JOIN users u ON ts.graded_by = u.id
        WHERE ts.student_id = %s
        ORDER BY ts.submitted_at DESC
    """, (g.user['id'],))
    submissions = cur.fetchall()
    
    return render_template('my_task_scores.html', submissions=submissions)


# Alias untuk my_task_scores (untuk backward compatibility)
@app.route('/my-tasks')
@login_required
def my_tasks():
    """Redirect ke my_task_scores"""
    return redirect(url_for('my_task_scores'))


# === SISWA: LIHAT UPLOAD MEREKA ===
@app.route('/my-submissions')
@login_required
def my_submissions():
    """Siswa melihat semua file yang telah diupload"""
    if g.user.get('role') != 'student':
        flash("Halaman ini hanya untuk siswa.")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("""
        SELECT ts.*, t.title as task_title
        FROM task_submissions ts
        JOIN tasks t ON ts.task_id = t.id
        WHERE ts.student_id = %s
        ORDER BY ts.submitted_at DESC
    """, (g.user['id'],))
    submissions = cur.fetchall()
    
    return render_template('my_submissions.html', submissions=submissions)


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
        avatar_filename = user.get('avatar')

        # Cek apakah ada data avatar dari cropper (base64)
        avatar_data = request.form.get('avatar')
        
        if avatar_data and avatar_data.startswith('data:image'):
            try:
                # Parse base64 data
                # Format: data:image/jpeg;base64,/9j/4AAQSkZJRg...
                header, encoded = avatar_data.split(',', 1)
                
                # Decode base64
                import base64
                from PIL import Image
                import io
                
                image_data = base64.b64decode(encoded)
                
                # Open image dengan PIL untuk resize konsisten
                img = Image.open(io.BytesIO(image_data))
                
                # Resize ke ukuran standar 3:4 ratio (450x600)
                img = img.resize((450, 600), Image.LANCZOS)
                
                # Convert RGBA to RGB jika perlu
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                final_name = f"{g.user['username']}_{timestamp}_avatar.jpg"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], final_name)
                
                # Save file dengan quality optimization
                img.save(save_path, 'JPEG', quality=85, optimize=True)
                
                # Hapus avatar lama jika ada dan bukan default
                if avatar_filename and avatar_filename != 'default_avatar.png':
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], avatar_filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except:
                            pass
                
                avatar_filename = final_name
                
            except Exception as e:
                flash(f'Gagal menyimpan foto: {str(e)}')
                return redirect(url_for('edit_profile'))

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

# === FORUM DISKUSI (LENGKAP) ===
@app.route('/forum', methods=['GET', 'POST'])
@login_required
def forum():
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    if request.method == 'POST':
        title = request.form['title'].strip()
        body = request.form['body'].strip()
        
        if not title or not body:
            flash("Judul dan isi diskusi tidak boleh kosong.")
            return redirect(url_for('forum'))
        
        cur2 = db.cursor()
        cur2.execute("""
            INSERT INTO forum_posts (title, body, user_id, created_at) 
            VALUES (%s, %s, %s, %s)
        """, (title, body, g.user['id'], datetime.now()))
        db.commit()
        flash("Topik diskusi berhasil dibuat.")
        return redirect(url_for('forum'))
    
    # Filter dan sorting
    search = request.args.get('search', '').strip()
    sort = request.args.get('sort', 'latest')
    
    # Base query
    query = """
        SELECT p.*, u.username, u.full_name, u.role, u.avatar,
               (SELECT COUNT(*) FROM forum_replies WHERE post_id = p.id) as reply_count
        FROM forum_posts p
        LEFT JOIN users u ON u.id = p.user_id
    """
    
    params = []
    
    # Search filter
    if search:
        query += " WHERE p.title LIKE %s OR p.body LIKE %s"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
    
    # Sorting
    if sort == 'oldest':
        query += " ORDER BY p.created_at ASC"
    elif sort == 'popular':
        query += " ORDER BY reply_count DESC, p.created_at DESC"
    else:  # latest (default)
        query += " ORDER BY p.created_at DESC"
    
    if params:
        cur.execute(query, tuple(params))
    else:
        cur.execute(query)
    
    posts = cur.fetchall()
    return render_template('forum.html', posts=posts)


@app.route('/forum/post/<int:post_id>')
@login_required
def view_post(post_id):
    """Melihat detail post forum dengan semua balasan"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # Ambil data post
    cur.execute("""
        SELECT p.*, u.username, u.full_name, u.role, u.avatar
        FROM forum_posts p
        LEFT JOIN users u ON u.id = p.user_id
        WHERE p.id = %s
    """, (post_id,))
    post = cur.fetchone()
    
    if not post:
        flash("Topik diskusi tidak ditemukan.")
        return redirect(url_for('forum'))
    
    # Ambil semua balasan
    cur.execute("""
        SELECT r.*, u.username, u.full_name, u.role, u.avatar
        FROM forum_replies r
        LEFT JOIN users u ON u.id = r.user_id
        WHERE r.post_id = %s
        ORDER BY r.created_at ASC
    """, (post_id,))
    replies = cur.fetchall()
    
    return render_template('view_post.html', post=post, replies=replies)


@app.route('/forum/post/<int:post_id>/reply', methods=['POST'])
@login_required
def reply_post(post_id):
    """Membalas post forum"""
    body = request.form.get('body', '').strip()
    
    if not body:
        flash("Balasan tidak boleh kosong.")
        return redirect(url_for('view_post', post_id=post_id))
    
    db = get_db()
    cur = db.cursor()
    
    # Cek apakah post ada
    cur.execute("SELECT id FROM forum_posts WHERE id=%s", (post_id,))
    if not cur.fetchone():
        flash("Topik diskusi tidak ditemukan.")
        return redirect(url_for('forum'))
    
    # Insert reply
    cur.execute("""
        INSERT INTO forum_replies (post_id, user_id, body, created_at)
        VALUES (%s, %s, %s, %s)
    """, (post_id, g.user['id'], body, datetime.now()))
    db.commit()
    
    flash("Balasan berhasil ditambahkan.")
    return redirect(url_for('view_post', post_id=post_id))


@app.route('/forum/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    """Edit post forum (hanya pembuat atau admin)"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM forum_posts WHERE id=%s", (post_id,))
    post = cur.fetchone()
    
    if not post:
        flash("Topik diskusi tidak ditemukan.")
        return redirect(url_for('forum'))
    
    # Cek akses
    if post['user_id'] != g.user['id'] and g.user.get('role') != 'admin':
        flash("Anda tidak memiliki akses untuk mengedit topik ini.")
        return redirect(url_for('view_post', post_id=post_id))
    
    if request.method == 'POST':
        title = request.form['title'].strip()
        body = request.form['body'].strip()
        
        if not title or not body:
            flash("Judul dan isi diskusi tidak boleh kosong.")
            return render_template('edit_post.html', post=post)
        
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE forum_posts 
            SET title=%s, body=%s, updated_at=%s
            WHERE id=%s
        """, (title, body, datetime.now(), post_id))
        db.commit()
        
        flash("Topik diskusi berhasil diperbarui.")
        return redirect(url_for('view_post', post_id=post_id))
    
    return render_template('edit_post.html', post=post)


@app.route('/forum/post/<int:post_id>/delete')
@login_required
def delete_post(post_id):
    """Hapus post forum (hanya pembuat atau admin)"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM forum_posts WHERE id=%s", (post_id,))
    post = cur.fetchone()
    
    if not post:
        flash("Topik diskusi tidak ditemukan.")
        return redirect(url_for('forum'))
    
    # Cek akses
    if post['user_id'] != g.user['id'] and g.user.get('role') != 'admin':
        flash("Anda tidak memiliki akses untuk menghapus topik ini.")
        return redirect(url_for('view_post', post_id=post_id))
    
    cur2 = db.cursor()
    # Hapus semua replies terlebih dahulu
    cur2.execute("DELETE FROM forum_replies WHERE post_id=%s", (post_id,))
    # Hapus post
    cur2.execute("DELETE FROM forum_posts WHERE id=%s", (post_id,))
    db.commit()
    
    flash("Topik diskusi berhasil dihapus.")
    return redirect(url_for('forum'))


@app.route('/forum/reply/<int:reply_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_reply(reply_id):
    """Edit reply forum (hanya pembuat atau admin)"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM forum_replies WHERE id=%s", (reply_id,))
    reply = cur.fetchone()
    
    if not reply:
        flash("Balasan tidak ditemukan.")
        return redirect(url_for('forum'))
    
    # Cek akses
    if reply['user_id'] != g.user['id'] and g.user.get('role') != 'admin':
        flash("Anda tidak memiliki akses untuk mengedit balasan ini.")
        return redirect(url_for('view_post', post_id=reply['post_id']))
    
    if request.method == 'POST':
        body = request.form['body'].strip()
        
        if not body:
            flash("Isi balasan tidak boleh kosong.")
            return render_template('edit_reply.html', reply=reply)
        
        cur2 = db.cursor()
        cur2.execute("""
            UPDATE forum_replies 
            SET body=%s, updated_at=%s
            WHERE id=%s
        """, (body, datetime.now(), reply_id))
        db.commit()
        
        flash("Balasan berhasil diperbarui.")
        return redirect(url_for('view_post', post_id=reply['post_id']))
    
    return render_template('edit_reply.html', reply=reply)


@app.route('/forum/reply/<int:reply_id>/delete')
@login_required
def delete_reply(reply_id):
    """Hapus reply forum (hanya pembuat atau admin)"""
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    cur.execute("SELECT * FROM forum_replies WHERE id=%s", (reply_id,))
    reply = cur.fetchone()
    
    if not reply:
        flash("Balasan tidak ditemukan.")
        return redirect(url_for('forum'))
    
    # Cek akses
    if reply['user_id'] != g.user['id'] and g.user.get('role') != 'admin':
        flash("Anda tidak memiliki akses untuk menghapus balasan ini.")
        return redirect(url_for('view_post', post_id=reply['post_id']))
    
    post_id = reply['post_id']
    
    cur2 = db.cursor()
    cur2.execute("DELETE FROM forum_replies WHERE id=%s", (reply_id,))
    db.commit()
    
    flash("Balasan berhasil dihapus.")
    return redirect(url_for('view_post', post_id=post_id))

# ===== TAMBAHKAN ROUTE INI KE app.py =====

# === SISWA: LIHAT RIWAYAT KUIS ===
@app.route('/my-quiz-history')
@login_required
def my_quiz_history():
    """Siswa melihat semua riwayat kuis yang pernah dikerjakan"""
    if g.user.get('role') != 'student':
        flash("Halaman ini hanya untuk siswa.", "warning")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    try:
        # Ambil semua kuis yang pernah dikerjakan dengan nilai terbaru
        cur.execute("""
            SELECT 
                q.id as quiz_id,
                q.title as quiz_title,
                qs.id as score_id,
                qs.score,
                qs.graded_at,
                c.name as class_name,
                (SELECT COUNT(*) FROM quiz_questions WHERE quiz_id = q.id) as total_questions
            FROM quiz_scores qs
            JOIN quizzes q ON qs.quiz_id = q.id
            LEFT JOIN classes c ON q.class_id = c.id
            WHERE qs.student_id = %s
            ORDER BY qs.graded_at DESC
        """, (g.user['id'],))
        quiz_history = cur.fetchall()
        
        # Hitung statistik
        if quiz_history:
            scores = [h['score'] for h in quiz_history]
            avg_score = sum(scores) / len(scores)
            highest_score = max(scores)
            lowest_score = min(scores)
            total_quiz = len(quiz_history)
        else:
            avg_score = 0
            highest_score = 0
            lowest_score = 0
            total_quiz = 0
        
        stats = {
            'total_quiz': total_quiz,
            'avg_score': round(avg_score, 1),  # Diubah ke 1 desimal agar lebih rapi
            'highest_score': highest_score,
            'lowest_score': lowest_score
        }
        
        return render_template('my_quiz_history.html', quiz_history=quiz_history, stats=stats)
    
    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}", "danger")
        return redirect(url_for('dashboard'))
    finally:
        cur.close()


@app.route('/quiz/<int:qid>/history/<int:score_id>')
@login_required
def view_quiz_history_detail(qid, score_id):
    """Siswa melihat detail hasil kuis yang pernah dikerjakan"""
    if g.user.get('role') != 'student':
        flash("Akses ditolak.", "danger")
        return redirect(url_for('dashboard'))
    
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    try:
        # Ambil data score - pastikan score milik user yang login
        cur.execute("""
            SELECT 
                qs.id,
                qs.quiz_id,
                qs.score,
                qs.graded_at,
                q.title as quiz_title,
                c.name as class_name
            FROM quiz_scores qs
            JOIN quizzes q ON qs.quiz_id = q.id
            LEFT JOIN classes c ON q.class_id = c.id
            WHERE qs.id = %s 
            AND qs.student_id = %s 
            AND qs.quiz_id = %s
        """, (score_id, g.user['id'], qid))
        score = cur.fetchone()
        
        if not score:
            flash("Data kuis tidak ditemukan atau Anda tidak memiliki akses.", "danger")
            return redirect(url_for('my_quiz_history'))
        
        # Ambil detail jawaban dengan join ke pertanyaan
        cur.execute("""
            SELECT 
                qq.id as question_id,
                qq.question,
                qq.option_a,
                qq.option_b,
                qq.option_c,
                qq.option_d,
                qq.option_e,
                qq.correct_option,
                COALESCE(qa.selected_option, '') as selected_option,
                COALESCE(qa.is_correct, 0) as is_correct
            FROM quiz_questions qq
            LEFT JOIN quiz_answers qa ON qq.id = qa.question_id 
                AND qa.student_id = %s 
                AND qa.quiz_id = %s
            WHERE qq.quiz_id = %s
            ORDER BY qq.id
        """, (g.user['id'], qid, qid))
        answers = cur.fetchall()
        
        # Hitung statistik jawaban
        total_questions = len(answers)
        correct_answers = sum(1 for a in answers if a.get('is_correct'))
        wrong_answers = total_questions - correct_answers
        
        answer_stats = {
            'total': total_questions,
            'correct': correct_answers,
            'wrong': wrong_answers
        }
        
        return render_template('view_quiz_history_detail.html', 
                             score=score, 
                             answers=answers, 
                             answer_stats=answer_stats)
    
    except Exception as e:
        flash(f"Terjadi kesalahan: {str(e)}", "danger")
        return redirect(url_for('my_quiz_history'))
    finally:
        cur.close()

# === START APP ===
if __name__ == '__main__':
    # --- Tambahkan import di bagian atas file kamu ---
    from pyngrok import ngrok, conf
    import webbrowser  # opsional: biar otomatis buka browser

    # --- Buat user default (jika belum ada) ---
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                INSERT IGNORE INTO users (username,password,role,full_name)
                VALUES (%s,%s,%s,%s)
            """, ("admin", generate_password_hash("admin123"), "admin", "Administrator"))
            cur.execute("""
                INSERT IGNORE INTO users (username,password,role,full_name)
                VALUES (%s,%s,%s,%s)
            """, ("sensei", generate_password_hash("sensei123"), "sensei", "Sensei Ichiro"))
            cur.execute("""
                INSERT IGNORE INTO users (username,password,role,full_name)
                VALUES (%s,%s,%s,%s)
            """, ("siswa", generate_password_hash("siswa123"), "student", "Siswa Aiko"))
            db.commit()
        except Exception as e:
            print("⚠️ Perhatikan: gagal insert default users (mungkin tabel belum dibuat):", e)

    # --- Jalankan ngrok ---
    try:
        conf.get_default().auth_token = "34utbZYQl80GDch5ccZw57PfVZm_659m5PdLnM5A54CYeHXTY"
        ngrok.kill()  # 🧹 hentikan tunnel lama agar tidak bentrok
        public_url = ngrok.connect(addr=5000)
        print(f"✅ Akses Flask kamu di URL ini: {public_url.public_url}")

        # (Opsional) Buka otomatis di browser
        webbrowser.open(public_url.public_url)

    except Exception as e:
        print("❌ Gagal membuat tunnel ngrok:", e)

    # --- Jalankan Flask ---
    app.run(debug=True, host='0.0.0.0', port=5000)
