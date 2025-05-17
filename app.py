from flask import Flask, render_template, request, redirect
import pandas as pd
import os
from flask_sqlalchemy import SQLAlchemy
from models import db, Record
from datetime import datetime
from sqlalchemy import extract, func, and_

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'records.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

DATA_PATH = "data/records.xlsx"

# 파일 없으면 새로 생성
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(DATA_PATH):
    df = pd.DataFrame(columns=["일자", "거래처", "품목", "수량", "단가", "공급가액", "세액", "합계"])
    df.to_excel(DATA_PATH, index=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        date = datetime.strptime(request.form["일자"], "%Y-%m-%d").date()
        client = request.form["거래처"]
        item = request.form["품목"]
        quantity = int(request.form["수량"])
        price = int(request.form["단가"])
        supply_price = quantity * price
        tax = int(supply_price * 0.1)
        total = supply_price + tax

        record = Record(
            date=date,
            client=client,
            item=item,
            quantity=quantity,
            price=price,
            supply_price=supply_price,
            tax=tax,
            total=total
        )
        db.session.add(record)
        db.session.commit()
        return redirect("/")

    records = Record.query.order_by(Record.date.desc()).all()
    return render_template("index.html", records=records)

from collections import defaultdict

@app.route("/statistics")
def statistics():
    # 쿼리 파라미터 받기
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    client = request.args.get("client", type=str)
    item = request.args.get("item", type=str)

    # 기본 쿼리
    query = db.session.query(
        extract('year', Record.date).label('year'),
        extract('month', Record.date).label('month'),
        func.sum(Record.supply_price).label('supply_sum'),
        func.sum(Record.tax).label('tax_sum'),
        func.sum(Record.total).label('total_sum')
    )

    # 조건 동적 추가
    filters = []
    if year:
        filters.append(extract('year', Record.date) == year)
    if month:
        filters.append(extract('month', Record.date) == month)
    if client:
        filters.append(Record.client == client)
    if item:
        filters.append(Record.item == item)

    if filters:
        query = query.filter(and_(*filters))

    query = query.group_by('year', 'month').order_by('year', 'month')
    stats = query.all()

    # 거래처, 품목 목록도 전달 (필터 select용)
    clients = db.session.query(Record.client).distinct().all()
    items = db.session.query(Record.item).distinct().all()

    # 월별 거래 추이 (연,월별 총합)
    monthly = (
        db.session.query(
            extract('year', Record.date).label('year'),
            extract('month', Record.date).label('month'),
            func.sum(Record.total).label('total_sum')
        )
        .group_by('year', 'month')
        .order_by('year', 'month')
        .all()
    )

    # 월별 라벨 리스트 생성
    monthly_labels = [f"{int(y)}-{int(m):02d}" for y, m, *_ in monthly]
    monthly_data = [int(t) if t is not None else 0 for *_, t in monthly]

    # 품목별 비율
    item_ratio = (
        db.session.query(
            Record.item,
            func.sum(Record.total).label('total_sum')
        )
        .group_by(Record.item)
        .order_by(func.sum(Record.total).desc())
        .all()
    )
    item_labels = [i for i, _ in item_ratio]
    item_data = [int(t) if t is not None else 0 for _, t in item_ratio]

    return render_template(
        "statistics.html",
        stats=stats,
        year=year,
        month=month,
        client=client,
        item=item,
        clients=[c[0] for c in clients],
        items=[i[0] for i in items],
        monthly_labels=monthly_labels,
        monthly_data=monthly_data,
        item_labels=item_labels,
        item_data=item_data
    )

if __name__ == "__main__":
    app.run(debug=True)