from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pillbox.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
scheduler = BackgroundScheduler()
scheduler.start()

# Database Model
class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(10))
    stock = db.Column(db.Integer)
    taken_today = db.Column(db.Boolean, default=False)

# Create database
with app.app_context():
    db.create_all()

# Reminder function
def send_reminder():
    print("🔔 Time to take your medicine!")

    # Second reminder after 10 minutes
    scheduler.add_job(
        func=second_reminder,
        trigger="date",
        run_date=datetime.now() + timedelta(minutes=10)
    )

def second_reminder():
    print("⚠️ Did you take your medicine? Please confirm!")

# Home Page
@app.route('/')
def home():
        return render_template('home.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    med = Medicine.query.first()

    if request.method == 'POST':
        time = request.form['time']
        stock = int(request.form['stock'])

        if med is None:
            med = Medicine(time=time, stock=stock)
            db.session.add(med)
        else:
            med.time = time
            med.stock = stock

        db.session.commit()

        # Schedule reminder
        hour, minute = map(int, time.split(":"))
        scheduler.add_job(
            func=send_reminder,
            trigger='cron',
            hour=hour,
            minute=minute
        )

        return redirect(url_for('details'))

    return render_template('details.html', med=med)

# Mark as taken
@app.route('/taken')
def mark_taken():
    med = Medicine.query.first()
    if med:
        med.taken_today = True
        med.stock -= 1
        db.session.commit()

        if med.stock <= 2:
            print("⚠️ Medicine is about to finish!")

    return redirect(url_for('index'))

# Progress Page
@app.route('/progress')
def progress():
    med = Medicine.query.first()
    return render_template('progress.html', med=med)

if __name__ == '__main__':
    app.run(debug=True)