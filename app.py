from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bootstrap import Bootstrap
import pytz
from flask_sqlalchemy import SQLAlchemy
from flask import abort
from datetime import datetime
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
login_manager = LoginManager(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)
app.static_folder = 'static'
migrate = Migrate(app, db)
bootstrap = Bootstrap(app)
vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
current_time_utc = datetime.utcnow()
current_time_vn = current_time_utc.replace(tzinfo=pytz.utc).astimezone(vn_tz)
formatted_time = current_time_vn.strftime('%d-%m-%Y %H:%M:%S')

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    comments = db.relationship('Comment', backref='post_relation', lazy=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'role': self.role
        }

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post = db.relationship('Post', backref='post_comments')



class CommentForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Submit')
# Hàm tải người dùng
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Hàm để kiểm tra xem người dùng đã tồn tại trong hệ thống chưa
def is_user_exist(email):
    return User.query.filter_by(email=email).first() is not None

# Hàm để lấy ID mới cho người dùng
def get_new_user_id():
    last_user = User.query.order_by(User.id.desc()).first()
    return last_user.id + 1 if last_user else 1

# Hàm để lưu thông tin tài khoản vào cơ sở dữ liệu
def save_user(user):
    db.session.add(user)
    db.session.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        if keyword:
            posts = Post.query.filter(Post.title.ilike(f'%{keyword}%')).all()
            return render_template('index.html', posts=posts, keyword=keyword)
    posts = Post.query.all()
    # Truy vấn tất cả các bình luận của mỗi bài viết
    comments = {post.id: Comment.query.filter_by(post_id=post.id).all() for post in posts}
    return render_template('index.html', posts=posts, comments=comments)


# Bình luận
@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    if content:
        new_comment = Comment(content=content, post_id=post_id)  # Chuyển post_id từ tham số của hàm
        db.session.add(new_comment)
        db.session.commit()
    return redirect(url_for('index'))
 

@app.route('/post', methods=['GET', 'POST'])
def post():  
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        if keyword:
            # Thực hiện tìm kiếm nếu có keyword
            posts = Post.query.filter(Post.title.ilike(f'%{keyword}%')).all()
            return render_template('index.html', posts=posts, keyword=keyword)
    # Nếu không có keyword hoặc không có dữ liệu từ form, hiển thị tất cả các bài viết
    posts = Post.query.all()
    return render_template('posts.html', posts=posts)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/admin')
@login_required
def admin():
    if current_user.role == 1:  # Nếu role của user hiện tại là 1 (admin)
        posts = Post.query.all()
        return render_template('admin/admin.html', posts=posts)
    else:
        return "Unauthorized", 401  # Trả về mã lỗi 401 nếu user không phải admin
@app.route('/admin/comments')
@login_required
def admin_comments():
    if current_user.role != 1:  # Kiểm tra xem user có phải là admin không
        abort(403)  # Trả về lỗi 403 nếu không phải admin
        
    comments = Comment.query.all()  # Truy vấn tất cả các bình luận từ cơ sở dữ liệu
    return render_template('admin/comments.html', comments=comments)

@app.route('/admin/comment/<int:comment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    if current_user.role != 1:
        abort(403)  # Trả về lỗi 403 nếu không phải admin
    
    comment = Comment.query.get_or_404(comment_id)
    if request.method == 'POST':
        comment.content = request.form['content']
        db.session.commit()
        return redirect(url_for('admin_comments'))
    return render_template('admin/edit_comment.html', comment=comment)

@app.route('/admin/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    if current_user.role != 1:
        abort(403)  # Trả về lỗi 403 nếu không phải admin
    
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('admin_comments'))
@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword', '')
    # Thực hiện tìm kiếm bài viết dựa trên keyword ở đây
    posts = Post.query.filter(Post.title.ilike(f'%{keyword}%')).all()
    # Trả về kết quả tìm kiếm cho template
    return render_template('search_results.html', keyword=keyword, posts=posts)

# Trong hàm route '/admin/posts':
@app.route('/admin/posts')
@login_required
def admin_posts():
    if not current_user.role != 1:
        abort(403)  # Từ chối truy cập nếu không phải là admin

    # Lấy tất cả các bài viết, bao gồm cả những bài viết đã được phê duyệt
    all_posts = Post.query.all()

    return render_template('admin/posts.html', posts=all_posts)

@app.route('/admin/posts/pending')
@login_required
def pending_posts():
    # Truy vấn các bài viết có trạng thái 'pending' từ cơ sở dữ liệu
    pending_posts = Post.query.filter_by(status='pending').all()
    # Trả về template 'pending_posts.html' với danh sách bài viết chờ duyệt
    return render_template('admin/pending_posts.html', pending_posts=pending_posts)
# Route để phê duyệt hoặc từ chối bài viết
@app.route('/admin/posts/<int:post_id>/approve', methods=['POST'])
@login_required
def approve_post(post_id):
    if not current_user.role != 1:
        abort(403)  # Từ chối truy cập nếu không phải là admin

    post = Post.query.get_or_404(post_id)
    post.status = 'approved'  # Cập nhật trạng thái bài viết thành đã phê duyệt
    db.session.commit()

    flash('Bài viết đã được phê duyệt.', 'success')
    return redirect(url_for('admin_posts'))

@app.route('/admin/posts/<int:post_id>/reject', methods=['POST'])
@login_required
def reject_post(post_id):
    if not current_user.role != 1:
        abort(403)  # Từ chối truy cập nếu không phải là admin

    post = Post.query.get_or_404(post_id)
    post.status = 'rejected'  # Cập nhật trạng thái bài viết thành từ chối
    db.session.commit()

    flash('Bài viết đã bị từ chối.', 'danger')
    return redirect(url_for('admin_posts'))

@app.route('/admin/users/set-role/<int:user_id>', methods=['POST'])
@login_required
def set_role(user_id):
    user = User.query.get_or_404(user_id)
    role = request.form.get('role')
    user.role = int(role)
    db.session.commit()
    flash('Đã cập nhật role cho người dùng.', 'success')
    return redirect(url_for('admin'))

@app.route('/userManagement')
@login_required
def user_management():
    users = User.query.all()
    return render_template('admin/userManagement.html', users=users)


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Xóa tài khoản thành công.', 'success')
    return redirect(url_for('admin'))


# Trong hàm route '/create':
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image_url = None
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        new_post = Post(title=title, content=content, image_url=image_url, status='pending')
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create.html')


@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        if 'new_image' in request.files:
            new_image = request.files['new_image']
            if new_image and allowed_file(new_image.filename):
                filename = secure_filename(new_image.filename)
                new_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                post.image_url = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', post=post)

@app.route('/delete/<int:post_id>')
def delete(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Email hoặc mật khẩu không hợp lệ', 'error')
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    if request.method == 'POST':
        logout_user()
        return redirect(url_for('index'))
    else:
        return "Method Not Allowed", 405


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. You can now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/protected')
@login_required
def protected():
    return 'This is a protected page!'

if __name__ == '__main__':
    app.run(debug=True)
