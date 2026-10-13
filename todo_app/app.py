from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

#데이터베이스 위치
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db' #app.config : Flask의 설정을 담고 있는 객체, sqlite:///todo.db : 현재 디렉토리의 todo.db 파일을 사용
#flask의 SQLAlchemy모듈을 사용하기 위해 URI를 설정해주는 코드입니다. sqlite:///todo.db는 현재 디렉토리의 todo.db 파일을 사용하겠다는 의미입니다.

db = SQLAlchemy(app) #SQLAlchemy 객체를 생성하고, Flask 앱과 연결합니다. db는 데이터베이스와 상호작용하는 데 사용됩니다.

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    done = db.Column(db.Boolean, default=False)
    note = db.Column(db.String(200))

    def __repr__(self):
        return f'<Todo {self.id} {self.text}>'

#간단한 in-memory데이터 저장소
todos=[]

@app.route('/', methods = ['GET', 'POST'])
def index():
    if request.method == 'POST':
        db.session.add(Todo(text=request.form['todo'], note=request.form['note'])) #데이터 추가
        db.session.commit() #commit : 변경 사항 저장
        return redirect(url_for('index')) #index호출

    todos = Todo.query.all()
    return render_template('index.html', todos=todos)

@app.route('/delete/<int:id>')
def delete(id):
    todo = db.get_or_404(Todo, id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/toggle/<int:id>')
def toggle(id):
    todo = db.get_or_404(Todo, id)
    todo.done = not todo.done
    db.session.commit()
    return redirect(url_for('index'))


#route를 모두 정의한 후에 데이터베이스 테이블을 생성합니다. 이유는 Flask-SQLAlchemy는 앱이 실행될 때 데이터베이스 테이블을 생성하기 때문에, route를 정의하기 전에 테이블을 생성하면 route에서 정의한 모델이 반영되지 않을 수 있습니다. 따라서 route를 모두 정의한 후에 데이터베이스 테이블을 생성하는 것이 좋습니다.
with app.app_context():
    db.create_all()  # 데이터베이스 테이블 생성

if __name__ == '__main__':
    app.run(debug=True)