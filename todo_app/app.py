from flask import Flask, Blueprint, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource, fields

app = Flask(__name__)

# 데이터베이스 위치
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///todo.db"  # app.config : Flask의 설정을 담고 있는 객체, sqlite:///todo.db : 현재 디렉토리의 todo.db 파일을 사용
)
# flask의 SQLAlchemy모듈을 사용하기 위해 URI를 설정해주는 코드입니다. sqlite:///todo.db는 현재 디렉토리의 todo.db 파일을 사용하겠다는 의미입니다.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# 404 에 "did you mean ...?" 라는 긴 안내가 따라붙는 것을 끕니다.
app.config["ERROR_404_HELP"] = False
# 한글을 \uc6b0\uc720 처럼 바꾸지 않고 그대로 내보냅니다.
app.config["RESTX_JSON"] = {"ensure_ascii": False}

db = SQLAlchemy(
    app
)  # SQLAlchemy 객체를 생성하고, Flask 앱과 연결합니다. db는 데이터베이스와 상호작용하는 데 사용됩니다.


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    done = db.Column(db.Boolean, default=False)
    note = db.Column(db.String(200))

    def __repr__(self):
        return f"<Todo {self.id} {self.text}>"


# 간단한 in-memory데이터 저장소
todos = []


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        db.session.add(
            Todo(text=request.form["todo"], note=request.form["note"])
        )  # 데이터 추가
        db.session.commit()  # commit : 변경 사항 저장
        return redirect(url_for("index"))  # index호출

    todos = Todo.query.all()
    return render_template("index.html", todos=todos)


@app.route("/delete/<int:id>")
def delete(id):
    todo = db.get_or_404(Todo, id)
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for("index"))


@app.route("/toggle/<int:id>")
def toggle(id):
    todo = db.get_or_404(Todo, id)
    todo.done = not todo.done
    db.session.commit()
    return redirect(url_for("index"))


# ------------------------------------------------------------------------- API
# Blueprint 로 한 번 감싸고 거기에 Api 를 붙입니다.
# 이렇게 해야 /api 아래에서만 JSON 이 나오고, 위의 화면 라우트는 그대로 남습니다.
api_bp = Blueprint("api", __name__, url_prefix="/api")

#전체적인 api기본 설정
api = Api(
    api_bp,
    version="1.0",
    title="Todo API",
    description="4장에서 만든 todo 앱의 API",
    doc="/docs",  # 문서는 /api/docs 에 열립니다
)
ns = api.namespace("todos", description="할 일 하나하나를 다루는 곳")

# 주고받을 데이터의 모양
todo_model = api.model(
    "Todo",
    {
        "id": fields.Integer(readonly=True, description="줄 번호. 서버가 붙입니다"),
        "text": fields.String(
            required=True, description="할 일 글자", example="우유 사기"
        ),
        "done": fields.Boolean(description="완료 여부", example=False),
    },
)

# 입력받는 데이터 형식
todo_input = api.model(
    "TodoInput",
    {
        "text": fields.String(
            required=True, description="할 일 글자", example="우유 사기"
        ),
        "done": fields.Boolean(description="완료 여부", example=False),
    },
)


@ns.route("/") #api/todos/경로에서
class TodoList(Resource):
    @ns.doc("목록 보기") #ns.doc : 문서 설명
    @ns.marshal_list_with(todo_model)
    def get(self):
        """할 일을 전부 돌려준다"""
        return Todo.query.all()

    @ns.doc("새로 만들기")
    @ns.expect(todo_input, validate=True)
    @ns.marshal_with(todo_model, code=201)
    def post(self):
        """할 일을 하나 데이터베이스에 추가하고, 넣은 일 표시"""
        todo = Todo(text=api.payload["text"], done=api.payload.get("done", False))
        db.session.add(todo)
        db.session.commit()
        # 만들었으면 201 과 함께 그것이 어디 있는지 Location 에 적어 줍니다.
        return todo, 201, {"Location": f"/api/todos/{todo.id}"}


@ns.route("/<int:id>")
@ns.param("id", "할 일의 줄 번호")
@ns.response(404, "그 번호의 할 일이 없습니다")
class TodoItem(Resource):
    @ns.doc("하나 보기")
    @ns.marshal_with(todo_model)
    def get(self, id):
        """할 일 하나를 돌려준다"""
        return get_or_abort(id)

    @ns.doc("통째로 바꾸기")
    @ns.expect(todo_input, validate=True)
    @ns.marshal_with(todo_model)
    def put(self, id):
        """할 일 하나를 통째로 바꾼다. 보내지 않은 칸은 기본값이 된다"""
        todo = get_or_abort(id)
        todo.text = api.payload["text"]
        todo.done = api.payload.get("done", False)
        db.session.commit()
        return todo

    @ns.doc("일부만 바꾸기")
    @ns.expect(todo_input)
    @ns.marshal_with(todo_model)
    def patch(self, id):
        """text면 text만, done이면 done만 바꾼다"""
        todo = get_or_abort(id)
        if "text" in api.payload:
            todo.text = api.payload["text"]
        if "done" in api.payload:
            todo.done = api.payload["done"]
        db.session.commit()
        return todo

    @ns.doc("지우기")
    @ns.response(204, "지웠습니다. 돌려줄 내용이 없습니다")
    def delete(self, id):
        """할 일 하나를 지운다"""
        todo = get_or_abort(id)
        db.session.delete(todo)
        db.session.commit()
        return "", 204

#id에 따른 todo클래스를 가져오는 함수.
def get_or_abort(id):
    """없는 번호면 404 를 JSON 으로 돌려준다."""
    todo = db.session.get(Todo, id)
    if todo is None:
        # abort 에 넘긴 것이 그대로 JSON 의 message 가 됩니다.
        ns.abort(404, f"{id} 번 할 일이 없습니다")
    return todo


app.register_blueprint(api_bp)

# route를 모두 정의한 후에 데이터베이스 테이블을 생성합니다. 이유는 Flask-SQLAlchemy는 앱이 실행될 때 데이터베이스 테이블을 생성하기 때문에, route를 정의하기 전에 테이블을 생성하면 route에서 정의한 모델이 반영되지 않을 수 있습니다. 따라서 route를 모두 정의한 후에 데이터베이스 테이블을 생성하는 것이 좋습니다.
with app.app_context():
    db.create_all()  # 데이터베이스 테이블 생성

if __name__ == "__main__":
    app.run(debug=True)
