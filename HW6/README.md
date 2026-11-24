# HW6
이름 · 학번 : 24011300 박진우

## 실행 방법
가상환경 (`venv`) 을 켠 뒤 jupyter (또는 VSCode) 로 `hw6.ipynb` 를 열고 `Run All`.
`sales_clean.csv` 가 같은 폴더에 있어야 하며, 노트북이 `sales_model.pkl` (linear regression + qp) 을 만듭니다.
API : 같은 폴더에서 `flask --app app run` 뒤 http://127.0.0.1:5000/api/docs
(`POST /api/sales/predict` 에 `{"quantity": 40, "unit_price": 200000}` → `{"total_sales": 8000000}`)

## 단계 ③ 답
총액 = 수량 × 단가 인 곱셈 관계인데, linear regression 은 a × 수량 + b × 단가 + c 처럼 더하는 모양(평면)만 만들 수 있어 곱셈을 표현하지 못한다 (test R² 0.862).
수량 × 단가 열 `qp` 를 feature 로 더하면 총액이 qp 에 대한 직선이 되어, model 이 계수 [0, 0, 1] · 절편 0 으로 공식을 그대로 찾아낸다 (test R² 1.0).

## 단계 ⑤ 결정과 이유
cross-validation (cv=5) 평균은 max_depth 3 : 0.845, 5 : 0.961, 8 : 0.992, 12 : 0.995, 제한 없음 : 0.994 로 depth 8 부터 거의 같다 (표준편차 0.000).
score 가 거의 같으면 단순한 쪽을 고르므로 **max_depth 8** (잎 250 개) 을 고른다. 잎 781 개인 depth 12 와의 차이는 0.003 뿐이다.
training 1.000 과 test 0.994 의 차이가 작은 것은 「총액 = 수량 × 단가」 라는 규칙이 실제로 있는 문제라 외워도 test 에서 그대로 통하기 때문이다.

## 단계 ⑦ 답
API 에는 **linear regression + qp** 를 올린다. 수량 40 · 단가 200,000 에 대해 linear + qp 는 8,000,000, 실제 곱도 8,000,000 으로 정확히 같다.
decision tree (max_depth 8) 는 test R² 0.991 로 점수는 높지만 7,362,301 을 답해 약 64만 원(8%) 틀린다. tree 는 training 에서 본 구간의 평균(계단)으로만 답하므로 데이터가 드문 범위나 범위 밖에서 더 벗어난다.
단, 서버에서도 학습 때처럼 `qp` 열을 똑같이 만들어 넣어야 한다 (app.py 의 `x["qp"] = ...`). 공식이 있는 문제이므로 실제 서비스라면 model 없이 곱하는 편이 가장 정확하고 단순하다.
