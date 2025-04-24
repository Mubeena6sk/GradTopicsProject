from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, FileField
from wtforms.validators import DataRequired, Length, NumberRange, Regexp
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey123' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback_dev_key')


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    cover = db.Column(db.String(100), nullable=True)

class BookForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[
            DataRequired(message="Title is required."),
            Length(min=1, max=100, message="Title must be between 1 and 100 characters."),
            Regexp(r'^[A-Za-z0-9 ,.\'-]+$', message="Title contains invalid characters.")
        ]
    )

    author = StringField(
        'Author',
        validators=[
            DataRequired(message="Author is required."),
            Length(min=1, max=100, message="Author must be between 1 and 100 characters."),
            Regexp(r'^[A-Za-z .\-]+$', message="Author name contains invalid characters.")
        ]
    )

    rating = FloatField(
        'Rating',
        validators=[
            DataRequired(message="Rating is required."),
            NumberRange(min=0, max=5, message="Rating must be between 0 and 5.")
        ]
    )

    cover = FileField(
        'Book Cover',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPG and PNG images are allowed.')
        ]
    )
    submit = SubmitField('Submit')

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/assignment/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/assignment/')
        except:
            return 'There was an issue adding your task'

    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('assignment/index.html', tasks=tasks)


@app.route('/assignment/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/assignment/')
    except:
        return 'There was a problem deleting that task'

@app.route('/assignment/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/assignment/')
        except:
            return 'There was an issue updating your task'

    else:
        return render_template('assignment/update.html', task=task)
    
@app.route('/project/')
def indexx():
    return render_template('project/index.html')

@app.route('/project/books/')
def books():
    sort = request.args.get('sort_by', 'title')
    books = Book.query.order_by(getattr(Book, sort)).all()
    return render_template('project/books.html', books=books, sort=sort)

@app.route('/project/add/', methods=['GET', 'POST'])
def add():
    form = BookForm()
    if form.validate_on_submit():
        filename = None
        if form.cover.data:
            filename = secure_filename(form.cover.data.filename)
            form.cover.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        new_book = Book(title=form.title.data, author=form.author.data, rating=form.rating.data, cover=filename)
        db.session.add(new_book)
        db.session.commit()
        flash('Book added!')
        return redirect(url_for('books'))
    return render_template('project/add_book.html', form=form)

@app.route('/project/edit/<int:book_id>/', methods=['GET', 'POST'])
def edit(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)
    if form.validate_on_submit():
        if form.cover.data:
            filename = secure_filename(form.cover.data.filename)
            form.cover.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            book.cover = filename
        book.title = form.title.data
        book.author = form.author.data
        book.rating = form.rating.data
        db.session.commit()
        flash('Book updated!')
        return redirect(url_for('books'))
    return render_template('project/edit_book.html', form=form, book=book)

@app.route('/project/delete/<int:book_id>/', methods=['GET', 'POST'])
def deletee(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted!')
    return redirect(url_for('books'))

@app.route('/project/uploads/<filename>/')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/project/chart/')
def chart():
    data = Book.query.all()
    titles = [book.title for book in data]
    ratings = [book.rating for book in data]
    return render_template('project/charts.html', titles=titles, ratings=ratings)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


# if __name__ == "__main__":
#     app.run(debug=True)
