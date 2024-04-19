from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient, DESCENDING
from bson import ObjectId
from dotenv import load_dotenv
import datetime
import os

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

client = MongoClient(os.environ.get('MONGODB_URI'))
db = client[os.environ.get('DB_NAME')]

app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET_KEY')

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/fruits')
def fruits():
    fruit_collection = list(db.fruits.find().sort('_id', DESCENDING))
    return render_template('fruits.html', fruit_collection=fruit_collection)

@app.route('/fruit/add', methods=['GET', 'POST'])
def add_fruit():
    if request.method == 'GET':
        return render_template('add-fruit.html')
    else:
        name = request.form.get('name')
        price = int(request.form.get('price'))
        description = request.form.get('description')
        image = request.files['image']
        filename = None

        if image:
            save_to = 'static/uploads'
            if not os.path.exists(save_to):
                os.makedirs(save_to)

            ext = image.filename.split('.')[-1]
            filename = f"fruit-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.{ext}"
            image.save(f"{save_to}/{filename}")

        db.fruits.insert_one({ 
            "name": name, 
            "price": price, 
            "description": description, 
            "image": filename 
        })

        flash('Fruit added successfully!')
        return redirect(url_for('fruits'))

@app.route('/fruit/edit/<id>', methods=['GET', 'POST'])
def edit_fruit(id):
    if request.method == 'GET':
        fruit = db.fruits.find_one({'_id': ObjectId(id)})
        return render_template('edit-fruit.html', fruit=fruit)
    else:
        name = request.form.get('name')
        price = int(request.form.get('price'))
        description = request.form.get('description')
        image = request.files['image']

        if image:
            fruit = db.fruits.find_one({'_id': ObjectId(id)})
            save_to = 'static/uploads'
            target = f"{save_to}/{fruit['image']}"
            
            if os.path.exists(target):
                os.remove(target)

            ext = image.filename.split('.')[-1]
            filename = f"fruit-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.{ext}"
            image.save(f"{save_to}/{filename}")

            db.fruits.update_one({ '_id': ObjectId(id) }, { '$set': { 'image': filename }})
        
        db.fruits.update_one({'_id': ObjectId(id)}, {'$set': {
            'name': name, 'price': price, 'description': description
        }})

        flash('Fruit updated successfully!')
        return redirect(url_for('fruits'))

@app.route('/fruit/delete/<id>', methods=['POST'])
def delete_fruit(id):
    fruit = db.fruits.find_one({'_id': ObjectId(id)})
    target = f"static/uploads/{fruit['image']}"

    if os.path.exists(target):
        os.remove(target)
    
    db.fruits.delete_one({'_id': ObjectId(id)})
    
    flash('Fruit deleted successfully!')
    return redirect(url_for('fruits'))

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)