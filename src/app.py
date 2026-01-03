"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Favorites, People, Planet, FavoritePeople, FavoritePlanet

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200


#### GET Endpoints

@app.route('/users', methods=['GET'])
def get_users():
    all_users = User.query.all()
    all_users = list(map(lambda u: u.serialize(), all_users))
    return jsonify(all_users), 200

#People

@app.route('/people', methods=['GET'])
def get_people():
    people = People.query.all()
    if not len(people) > 0:
        return jsonify({"error": "not found"}), 404
    all_people = list(map(lambda p: p.serialize(), people))
    return jsonify(all_people), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = People.query.get(people_id)
    if person is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(person.serialize()), 200

#Planets

@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    if not len(planets) > 0:
        return jsonify({"error": "not found"}), 404
    all_planets = list(map(lambda x: x.serialize(), planets))
    return jsonify(all_planets), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):

    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "not found"}), 404
    return jsonify(planet.serialize()), 200

######### FAVORITES

#### GET 

@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    all_favorites = Favorites.query.filter_by(user_id=user_id).all()
    if not all_favorites:
        return jsonify({"error": "not found"}), 404
    user_fav = []
    for f in all_favorites:
        user_fav.append(f.serialize())
    return jsonify(user_fav), 200

#### POST 

app.route("/favorite/people/<int:people_id>", methods=["POST"])
def add_favorite_person(people_id, user_id):
    people = People.query.get(people_id)
    user = People.query.get(user_id)
    if not user:
       return jsonify({"error": "not found"}), 404
    if not people:
       return jsonify({"error": "not found"}), 404
    
    exist_favorite = FavoritePeople.query.filter_by(user_id=user_id, people_id=people_id).first()
    if exist_favorite: 
        return jsonify({"msg": "Character already in favorites"}), 400

    add_favorite = FavoritePeople(user_id=user_id, people_id=people_id)
    db.session.add(add_favorite)
    db.session.commit()
    return jsonify(add_favorite.serialize()), 200

app.route("/favorite/planets/<int:planet_id>", methods=["POST"])
def add_favorite_planet(planet_id, user_id):
    planet = People.query.get(planet_id)
    user = People.query.get(user_id)
    if not user:
       return jsonify({"error": "not found"}), 404
    if not planet:
       return jsonify({"error": "not found"}), 404
    
    exist_favorite = FavoritePlanet.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if exist_favorite: 
        return jsonify({"msg": "Planet already in favorites"}), 400

    add_favorite = FavoritePlanet(user_id=user_id, planet_id=planet_id)
    db.session.add(add_favorite)
    db.session.commit()
    return jsonify(add_favorite.serialize()), 200

#### DELETE 

@app.route("/favorite/people/<int:people_id>", methods=["DELETE"])
def delete_people_favorite(people_id, user_id):
    fav = FavoritePeople.query.filter_by(user_id = user_id , person_id = people_id).first()
    if not fav:
        return jsonify({"msg": "Favorite character not found"}), 400
    
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg" : "Character removed from favorites"}), 200


@app.route("/favorite/planet/<int:planet_id>", methods=["DELETE"])
def delete_planet_favorite(planet_id, user_id):
    fav = FavoritePlanet.query.filter_by(user_id = user_id , person_id = planet_id).first()
    if not fav:
        return jsonify({"msg": "Favorite character not found"}), 400
    
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg" : "Planets removed from favorites"}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
