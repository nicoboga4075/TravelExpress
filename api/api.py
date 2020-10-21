import hashlib
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import jsonify, g, request, abort
from flask_api import FlaskAPI, status
from flask_cors import CORS
import jwt
import phonenumbers
from validate_email import validate_email

# Settings

# set FLASK_APP=api.py
# set FLASK_ENV=development
# set FLASK_DEBUG=1

# Initialisation de l'api

api = FlaskAPI(__name__)
CORS(api)

# Configuration de l'api

api.config['SECRET_KEY'] = 'ec3f0831f0978bdc130ebba668551da9afb8740938af64999364262d4ce06d71'


# Routing d'accueil

@api.route("/")
def welcome():
    return jsonify({'message': 'Bienvenue sur TravelExpress !'})


# Routing d'authentification

@api.route('/login/', methods=['POST'])
def login():
    try:

        # Get the list of emails

        temp = query_db('select email from api_user')

        # Email

        email = request.data.get('email')

        # Password

        password = request.data.get('password')

        # Check the email and the password

        if email != '':

            if email in temp:

                if password != '':

                    test_password = encrypt_string(password)

                    correct_password = query_db('select password from api_user where email=?',
                                                [email], one=True)[0]

                    if test_password == correct_password:

                        # Connexion well done

                        token = jwt.encode(
                            {'exp': datetime.utcnow() + timedelta(minutes=token_validity)},
                            api.config['SECRET_KEY'])

                        return {'token': token.decode('UTF-8')}

                    else:

                        abort(404, 'Password not correct')

                else:

                    abort(400, 'Password is mandatory')

            else:

                abort(404, 'The given email is not in the database')

        else:

            abort(400, 'Email is mandatory')

    except():

        abort(500)


# JSON api_user

def user(user_id, name, email, password, phone, authorized, forbiddens):
    return {'user_id': user_id,
            'name': name,
            'email': email,
            'password': password,
            'phone': phone,
            'authorized': authorized,
            'forbiddens': forbiddens
            }


# JSON trip

def trip(trip_id, driver, passengers, departure_date, arrival_date, origin, destination, cost, is_full):
    return {
        'trip_id': trip_id,
        'driver': driver,
        'passengers': passengers,
        'departure_date': departure_date,
        'arrival_date': arrival_date,
        'origin': origin,
        'destination': destination,
        'cost': cost,
        'is_full': is_full

    }


# Fonction de hashage pour les passwords

def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()

    return sha_signature


# Fonction de validation du name

def conditions_user_name(name):
    if name is not None:

        if type(name) == type(''):  # if name is a string

            if blank(name) > 255:

                abort(400, 'Maximum length for the name is 255 characters')


            elif blank(name) < 3:

                abort(400, "Minimum length for the name is 3 characters except for ' ' ")

        else:

            abort(400, 'The given name is not a string')

    else:

        abort(400, 'Name is mandatory')


# Fonction de validation de l'email

def conditions_email(email):
    # Get the list of emails

    temp = query_db('select email from api_user')

    # Check the email validations

    if email is not None:

        if type(email) == type(''):

            if validate_email(email) and not_blank(email):

                if len(email) > 255:

                    abort(400, 'Maximum length for the email is 255 characters')

                elif len(email) < 6:

                    abort(400, 'Minimum length for the email is 6 characters')

                elif email in temp:

                    abort(400, 'The given email exists already in the database')

            else:

                abort(400, 'The given email is not valid')


        else:

            abort(400, 'The given email is not a string')


    else:

        abort(400, 'Email is mandatory')


# Fonction de validation du phone

def conditions_phone(phone):
    if phone is not None:

        if type(phone) == type(''):

            try:

                temp = phonenumbers.parse(number=phone, region=None)

                if not (phonenumbers.is_valid_number(temp)):
                    abort(400, 'The given phone number is not valid')


            except phonenumbers.phonenumberutil.NumberParseException:

                abort(400, 'The given phone number raises exceptions')


        else:

            abort(400, 'The given phone number is not a string')


# Fonction de validation du password

def conditions_password(password):
    if password is not None:

        if type(password) == type(''):

            if len(password) > 255:

                abort(400, 'Maximum length for the password is 255 characters')

            elif len(password) < 6:

                abort(400, 'Minimum length for the password is 6 characters')

            else:

                pass

        else:

            abort(400, 'The given password is not a string')


    else:

        abort(400, 'Password is mandatory')


# Routings

@api.route('/user/', methods=['GET', 'PUT'])
def api_user():
    if True:

        if request.method == 'GET':

            try:

                users = query_db('select * from user order by user_id')

                for i in range(len(users)):
                    users[i] = user(users[i][0], users[i][1], users[i][2], users[i][3], users[i][4], users[i][5],
                                    users[i][6])

                return jsonify(users)

            except():

                abort(500)

        else:  # request.method == 'PUT'

            try:

                # Name

                name = request.data.get('name', None)

                conditions_user_name(name)

                # Email

                email = request.data.get('email', None)

                conditions_email(email)

                # Phone

                phone = request.data.get('phone', None)

                conditions_phone(phone)

                # Password

                password = request.data.get('password', None)

                conditions_password(password)

                password = encrypt_string(password)

                # Creation of the user

                insert_user = query_db('insert into user(name,email,password,phone) VALUES(?,?,?,?)',
                                       [name, email, password, phone], change=True)

                user_id = query_db('select last_insert_rowid()', one=True)[0]

                return user(user_id, name, email, password, phone, None, None), status.HTTP_201_CREATED


            except():

                abort(500)

    else:

        abort(401)


@api.route('/user/<int:user_id>/', methods=['GET', 'PATCH', 'DELETE'])
def api_user_id(user_id):
    if True:

        try:

            infos = query_db('select * from user where user_id=?', [user_id], one=True)

            if request.method == "GET":

                try:

                    if not infos:

                        abort(404, 'User not found with the given user_id')

                    else:

                        profil = user(infos[0], infos[1], infos[2], infos[3], infos[4], infos[5], infos[6])

                        return jsonify(profil), status.HTTP_200_OK

                except():

                    abort(500)


            elif request.method == "PATCH":

                try:

                    # Name

                    name = request.data.get('name', None)

                    conditions_user_name(name)

                    # Email

                    email = request.data.get('email', None)

                    if infos[2] != email:

                        conditions_email(email)

                    else:

                        pass

                    # Phone

                    phone = request.data.get('phone', None)

                    conditions_phone(phone)

                    # Password

                    password = request.data.get('password', None)

                    if infos[3] != password:

                        conditions_password(password)

                        password = encrypt_string(password)

                    else:

                        pass

                    # Preferences

                    authorized = request.data.get('authorized', None)

                    forbiddens = request.data.get('forbiddens', None)

                    # Update of the user

                    update_user = query_db(
                        'update user set name=?,email=?,password=?,phone=?,authorized=?,forbiddens=? where user_id=?',
                        [name, email, password, phone, authorized, forbiddens, user_id], change=True)

                    return user(user_id, name, email, password, phone, authorized, forbiddens), status.HTTP_200_OK


                except():

                    abort(500)

            else:  # request.method ='DELETE'

                try:

                    # Get the list of user_ids

                    liste = query_db('select user_id from user')

                    temp = []

                    for element in liste:
                        temp += element

                    if user_id in temp:

                        delete_user = query_db('delete from user where user_id=?', [user_id], change=True)

                        return {}, status.HTTP_204_NO_CONTENT

                    else:

                        abort(404, 'User has already been deleted or does not exist')


                except():

                    abort(500)

        except():

            abort(500)

    else:

        abort(401)


@api.route('/trip/', methods=['GET', 'PUT'])
def api_trip():
    if True:

        if request.method == 'GET':

            try:

                trips = query_db('select * from trip order by trip_id')

                for i in range(len(trips)):
                    trips[i] = trip(trips[i][0], trips[i][1], trips[i][2], trips[i][3], trips[i][4], trips[i][5],
                                    trips[i][6], trips[i][7], trips[i][8])

                return jsonify(trips)

            except():

                abort(500)

        else:  # request.method == 'PUT'

            try:

                # Driver

                driver = request.data.get('driver', None)

                # Passengers

                passengers = request.data.get('passengers', None)

                # Departure date

                departure_date = request.data.get('departure_date', None)

                # Arrival date

                arrival_date = request.data.get('arrival_date', None)

                # Origin

                origin = request.data.get('origin', None)

                # Destination

                destination = request.data.get('destination', None)

                # Cost

                cost = request.data.get('cost', None)

                # Creation of the trip

                insert_trip = query_db(
                    'insert into trip(driver,passengers,departure_date,arrival_date,origin,destination,cost) VALUES(?,?,?,?,?,?,?)',
                    [driver, passengers, departure_date, arrival_date, origin, destination, cost], change=True)

                trip_id = query_db('select last_insert_rowid()', one=True)[0]

                return trip(trip_id, driver, passengers, departure_date, arrival_date, origin, destination, cost, False
                            ), status.HTTP_201_CREATED

            except():

                abort(500)

    else:

        abort(401)


@api.route('/trip/<int:trip_id>/', methods=['GET', 'PATCH', 'DELETE'])
def trip_trip_id(trip_id):
    if True:

        try:

            infos = query_db('select * from trip where trip_id=?', [trip_id], one=True)

            if request.method == "GET":

                try:

                    if not infos:

                        abort(404, 'Trip not found with the given trip_id')

                    else:

                        profil = trip(infos[0], infos[1], infos[2], infos[3], infos[4], infos[5], infos[6],
                                      infos[7], infos[8])

                        return jsonify(profil), status.HTTP_200_OK

                except():

                    abort(500)


            elif request.method == "PATCH":

                try:

                    # Driver

                    driver = request.data.get('driver', None)

                    # Passengers

                    passengers = request.data.get('passengers', None)

                    # Departure date

                    departure_date = request.data.get('departure_date', None)

                    # Arrival date

                    arrival_date = request.data.get('arrival_date', None)

                    # Origin

                    origin = request.data.get('origin', None)

                    # Destination

                    destination = request.data.get('destination', None)

                    # Cost

                    cost = request.data.get('cost', None)

                    # Full

                    is_full = request.data.get('is_full', None)


                    # Update of the trip

                    update_trip = query_db(
                        'update trip set driver=?,passengers=?,departure_date=?,arrival_date=?,origin=?,destination=?,cost=?,is_full=? where user_id=?',
                        [driver, passengers, departure_date, arrival_date, origin, destination, cost, is_full,
                         is_full,trip_id], change=True)

                    return trip(trip_id, driver, passengers, departure_date, arrival_date, origin, destination, cost,
                                is_full), status.HTTP_200_OK


                except():

                    abort(500)

            else:  # request.method ='DELETE'

                try:

                    # Get the list of trip_ids

                    liste = query_db('select trip_id from trip')

                    temp = []

                    for element in liste:
                        temp += element

                    if trip_id in temp:

                        delete_user = query_db('delete from trip where trip_id=?', [trip_id], change=True)

                        return {}, status.HTTP_204_NO_CONTENT

                    else:

                        abort(404, 'Trip has already been deleted or does not exist')


                except():

                    abort(500)

        except():

            abort(500)

    else:

        abort(401)


# Routings d'erreurs

@api.errorhandler(400)  # Bad Request
def bad_request(e):
    return jsonify(error=str(e)), 400


@api.errorhandler(401)  # Unauthorized
def unauthorized(e):
    return jsonify(error=str(e)), 401


@api.errorhandler(403)  # Forbidden
def forbidden(e):
    return jsonify(error=str(e)), 403


@api.errorhandler(404)  # Resource not found
def resource_not_found(e):
    return jsonify(error=str(e)), 404


@api.errorhandler(405)  # Method not allowed
def method_not_allowed(e):
    return jsonify(error=str(e)), 405


@api.errorhandler(500)  # Internal Error Server
def internal_error_server(e):
    return jsonify(error=str(e)), 500


token_validity = 60  # minutes


# Token OAuth 2.0
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = request.headers['Authorization']

        if not token:
            abort(401, 'Token is missing !')

        try:
            data = jwt.decode(token, api.config['SECRET_KEY'])

        except:

            abort(401, 'Token is invalid !')

        return f(*args, **kwargs)

    return decorated


# Fonctions de repérage des espaces

def blank(string):
    res = len(string)

    for i in range(len(string)):

        if string[i] == ' ':
            res -= 1

    return res


def not_blank(string):
    boolean = False

    if len(string.split(' ')) == 1:
        boolean = True

    return boolean


DATABASE = 'TravelExpress.db'


# Ouverture de la connexion

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


# Fermeture de la connexion

@api.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Requête SQLite

def query_db(query, args=(), one=False, change=False):
    cur = get_db().execute(query, args)
    rv = None
    if change:
        get_db().commit()
    else:
        rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# Running de l'api

if __name__ == '__main__':
    api.run(debug=True)
