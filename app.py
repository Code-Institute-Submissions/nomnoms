import os
import ast
import json
from flask import Flask, render_template, redirect, request, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from os import path
if path.exists("env.py"):
  import env 

app = Flask(__name__)

app.config["MONGO_DBNAME"] = "TossedSalad"
app.config["MONGO_URI"] = os.getenv("MONGO_URI")

mongo = PyMongo(app)

# Reusable functions
def recipe_init():
    # initialise blank recipe document to include all possible options including those not returned by create recipe form
    blank_recipe = {'title': '',
    'ingredients': [],
    'steps': [],
    'category': '',
    'owner': '',
    'pin': ''}

    # add key value pairs for recipe filters and allow for additions/deletions to filter keywords at db level
    recipe_info = mongo.db.optionalTypes.find_one({'name': 'recipe_info'})
    for key in recipe_info['dietary']:
        blank_recipe[key] = 'off'
    
    for key in recipe_info['meal']:
        blank_recipe[key] = 'off'

    return blank_recipe

@app.route('/')
@app.route('/home')
def home():
    # Route for returning to homepage
    return render_template('index.html')

@app.route('/browse_recipes')
def browse_recipes():
    # Browse and find recipes for viewing
    recipes = mongo.db.scrambledeggs.find()
    return render_template('recipe.html', recipes = recipes)

@app.route('/create_recipe')
def create_recipe():
    # displays the create recipe page
    measurements_list = mongo.db.optionalTypes.find_one({'name': 'measurements'})['values']
    categories = mongo.db.optionalTypes.find_one({'name': 'recipe_type'})['values']
    recipe_info = mongo.db.optionalTypes.find_one({'name': 'recipe_info'})

    return render_template('create_recipe.html', measurements=measurements_list, categories=categories, recipe_info=recipe_info)

@app.route('/add_recipe/', methods=['POST'])
def add_recipe():
    # Adding a new recipe document to database
    
    # initialise recipe document
    recipe_to_add = recipe_init()

    if request.method == 'POST':
        recipe_holder = request.form.to_dict()
        # processing steps info from <textarea> into an array so each step 
        # can be treated separately upon retrieval from mongodb
        
        # steps_string_holder = recipe_holder['steps']
        # steps_string_holder = steps_string_holder.replace('"', "'")
        # steps_holder = steps_string_holder.replace('<p>', '"')
        steps_holder = recipe_holder['steps']

        # There is a need to replace any instances of double quotes to avoid errors when converting 
        # string to dict object using json.loads()
        # First replace any double quotes with single quotes
        steps_holder = steps_holder.replace('"', "'")
        # then replace <p> with double quotes, 
        # <p> simply used in place of double quotes in form data to avoid being replaced in first replace operation
        steps_holder = steps_holder.replace('<p>', '"')

        steps = steps_holder.split('<br>')
        if len(steps) >= 1 :
            steps.pop()
            for i, val in enumerate(steps):
                steps[i] = json.loads(val)
                
        recipe_holder['steps'] = steps
        # processing ingredients/quantity/measurement info from <textarea> 
        # into an array so each step can be treated separately upon retrieval from mongodb
        ingredients_holder = recipe_holder['ingredients']
        ingredients = ingredients_holder.split('<br>')
        if len(ingredients) >= 1:
            ingredients.pop()
            for i, val in enumerate(ingredients):
                ingredients[i] = ast.literal_eval(val)            
        recipe_holder['ingredients'] = ingredients

        # replace values in blank document with form data
        for key in recipe_holder:
            recipe_to_add[key] = recipe_holder[key]
        
        # insert new recipe document in db
        recipe_db_connection = mongo.db.scrambledeggs
        recipe_db_connection.insert_one(recipe_to_add)

    return redirect(url_for('create_recipe'))

@app.route('/edit_recipe')
def edit_recipe():
    return render_template('edit_recipe.html', doc_not_found=False)

@app.route('/find_recipe_to_edit', methods=['POST'])
def find_recipe_to_edit():
    if request.method == 'POST':
        pincode = request.form.to_dict()
        recipes = mongo.db.scrambledeggs.find({'pin':pincode['pin'], 'owner':pincode['owner']})
        no_of_docs = mongo.db.scrambledeggs.count_documents({'pin':pincode['pin']})
        
        if no_of_docs > 0:
            return render_template('choose_recipe_to_edit.html', recipes=recipes)
        else:
            return render_template('edit_recipe.html', doc_not_found=True)

    return redirect(url_for('home'))

@app.route('/update_recipe/<recipe_id>', methods=['POST'])
def update_recipe(recipe_id):
    recipe = mongo.db.scrambledeggs.find_one({'_id': ObjectId(recipe_id)})

    measurements_list = mongo.db.optionalTypes.find_one({'name': 'measurements'})['values']
    categories = mongo.db.optionalTypes.find_one({'name': 'recipe_type'})['values']
    recipe_info = mongo.db.optionalTypes.find_one({'name': 'recipe_info'})

    return render_template('update_recipe.html', recipe=recipe, measurements=measurements_list, categories=categories, recipe_info=recipe_info)
    

if __name__ =='__main__':
    app.run(host=os.environ.get('IP'), port=os.environ.get('PORT'), debug=True)