import sys

from flask import Flask, render_template, request, jsonify, abort, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres@localhost:5432/todoapp'
# db = SQLAlchemy(app, session_options={"expire_on_commit": False})
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)

    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)

    def __repr__(self):
        return f'<Todo {self.id} {self.description}>'

class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)

    todos = db.relationship('Todo', backref='list', lazy=True)

    def __repr__(self):
        return f'<TodoList {self.id} {self.name}>'

@app.route('/lists/create', methods=['POST'])
def create_list():
    error = False
    body = {}
 
    try:
        name = request.get_json()['name']
        todolist = TodoList(name=name)
        db.session.add(todolist)
        db.session.commit()
        body['id'] = todolist.id
        body['name'] = todolist.name
    except():
        db.session.rollback()
        error = True
        print(sys.exc_info)
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify(body)

@app.route('/todos/create', methods=['POST'])
def create_todo():
    error = False
    body = {}

    try:
        description = request.get_json()['description']
        list_id = request.get_json()['list_id']
        todo = Todo(description=description, completed=False, list_id=list_id)
        db.session.add(todo)
        db.session.commit()
        body['id'] = todo.id
        body['completed'] = todo.completed
        body['description'] = todo.description
    except Exception:
        db.session.rollback()
        error=True
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify(body)

@app.route('/lists/<list_id>/delete', methods=['DELETE'])
def delete_list(list_id):
    error = False

    try:
        list = TodoList.query.get(list_id)

        for todo in list.todos:
            db.session.delete(todo)

        db.session.delete(list)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
 
    if error:
        abort(500)
    else:
        return jsonify({'success': True})

@app.route('/todos/<todo_id>/delete', methods=['DELETE'])
def delete_todo(todo_id):
    error = False

    try:
        #Todo.query.filter_by(id=todo_id).delete()
        todo = Todo.query.get(todo_id)
        db.session.delete(todo)
        db.session.commit()
    except Exception:
        error = True
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return jsonify({ 'success': True })

@app.route('/lists/<list_id>/set-completed', methods=['POST'])
def set_completed_list(list_id):
    error = False

    try:
        list = TodoList.query.get(list_id)

        for todo in list.todos:
            todo.completed = True

        db.session.commit()
    except Exception:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return '', 200

@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
def set_completed_todo(todo_id):
    error = False

    try:
        completed = request.get_json()['completed']

        todo = Todo.query.get(todo_id)
        todo.completed = completed

        db.session.commit()
    except Exception:
        db.session.rollback()

        error = True
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return '', 200

@app.route('/lists/<list_id>')
def get_list_todos(list_id):
    return render_template('index.html',
    lists = TodoList.query.all(),
    active_list = TodoList.query.get(list_id),
    todos = Todo.query.filter_by(list_id=list_id).order_by('id').all())

@app.route('/')
def index():
    return redirect(url_for('get_list_todos', list_id=1))