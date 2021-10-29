from flask import Flask
from flask import render_template
from flask import request, flash, redirect, url_for
import os
from utils.db import get_db, close_db, sql_connection
from utils.forms import*
from utils.utils import isEmailValid, isPasswordValid, comprobarContraseñas, isEmailLoginValid, isPasswordLoginValid
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, g
import functools
from repository.data_repository import *
from flask import make_response


app = Flask(__name__)
app.secret_key = os.urandom(24)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view
    

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    try:
        if request.method == 'POST':

            nombre = request.form['nombre']
            email = request.form['email']
            password = request.form['password']
            confirmpassword = request.form['confirmpassword']

            error = None
            
            if not isEmailValid(email):
                error = "Correo invalido"
                flash(error)
            if not isPasswordValid(password):
                error = "La contraseña debe contener al menos una minúscula, una mayúscula, un caracter especial, un número y 8 caracteres"
                flash(error)

            if not comprobarContraseñas(password, confirmpassword):
                error = "Las contraseñas no coinciden"
                flash(error)

            user_email = consultar_usuario_reg(email,)
            if user_email is not None:
                error = "Correo ingresado ya existe."
                flash(error)

            if error is not None:
                return render_template("registro.html")
            else:
                password_cifrado = generate_password_hash(password)
                guardar_usuarios_reg(nombre, email, password_cifrado)

                return redirect(url_for('login'))

        rol_user = session.get('rol')
        if 'id_user' in session and rol_user == 'adm':
            return redirect(url_for('dashboard'))
        if 'id_user' in session and rol_user == 'user':
            return redirect(url_for('inicio_usuario'))
        if 'id_user' in session and rol_user == 'pilot':
            return redirect(url_for('piloto'))
        return render_template("registro.html")
    except:
        flash("¡Ups! Ha ocurrido un error, intentelo de nuevo.")
        return render_template("registro.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':

            email = request.form['email']
            password = request.form['password']

            error = None
            
            if not isEmailLoginValid(email):
                error = "Correo invalido"
                flash(error)
            if not isPasswordLoginValid(password):
                error = "La contraseña debe contener al menos una minúscula, una mayúscula, un caracter especial, un número y 8 caracteres"
                flash(error)

            if error is not None:
                return render_template("login.html")

            else:
                user = consultar_usuarios(email,)

                if user is None:
                    error = "Correo y/o contraseña no existe."
                    flash(error)
                    return render_template("login.html")
                else:
                    usuario_valido = check_password_hash(user[3], password)
                    if not usuario_valido:
                        error = "Usuario y/o contraseña no son correctos."
                        flash(error)
                        return render_template("login.html")
                    else:
                        session.clear()
                        session['id_user'] = user[0]
                        session['rol'] = user[4]
                        rol_usuario = session.get('rol')
                        if rol_usuario == 'adm':
                            response = make_response(redirect(url_for('dashboard')) )
                            response.set_cookie( 'username', email )
                            return response
                        if rol_usuario == 'user':
                            response = make_response( redirect(url_for('inicio_usuario')) )
                            response.set_cookie( 'username', email )
                            return response
                        if rol_usuario == 'pilot':
                            
                            response = make_response( redirect(url_for('piloto')) )
                            response.set_cookie( 'username', email )
                            return response

        rol = session.get('rol')
        if 'id_user' in session and rol == 'adm':
            return redirect(url_for('dashboard'))
        if 'id_user' in session and rol == 'user':
            return redirect(url_for('inicio_usuario'))
        if 'id_user' in session and rol == 'pilot':
            return redirect(url_for('piloto'))
        return render_template("login.html")
    except:
        flash("¡Ups! Ha ocurrido un error, intentelo de nuevo.")
        return render_template("login.html")


@app.before_request
def cargar_usuario_registrado():
    print("Entró en before_request.")
    id_usuario = session.get('id_user')
    if id_usuario is None:
        g.user = None
    else:
        """ g.user = get_db().execute(
            'SELECT * FROM usuarios WHERE idusuarios = ?'
            ,(id_usuario,)
        ).fetchone() """
        g.user = consultar_usuario_g(id_usuario)
    print("usuario", g.user)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    vuelos_llegada = consultar_vuelos_llegada()
    vuelos_salida = consultar_vuelos_salidas()
    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':
        return render_template('dashboard.html', vuelos_llegada=vuelos_llegada, vuelos_salida=vuelos_salida)
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/crear_usuario', methods=['GET', 'POST'])
@login_required
def crear_usuario():

    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':
        try:
            if request.method == 'POST':

                nombre = request.form['nombre']
                email = request.form['email']
                password = request.form['password']
                rol = "user"

                error = None
                db = get_db()

                if not isEmailValid(email):
                    error = "Correo invalido"
                    flash(error)
                if not isPasswordValid(password):
                    error = "La contraseña debe contener al menos una minúscula, una mayúscula, un caracter especial, un número y 8 caracteres"
                    flash(error)

                user_email = consultar_usuarios(email,)
                if user_email is not None:
                    error = "Correo ingresado ya existe."
                    flash(error)

                if error is not None:
                    return render_template("crear_usuario.html")
                else:
                    password_cifrado = generate_password_hash(password)

                    guardar_usuarios_pilot(
                        nombre, email, password_cifrado, rol)
                    flash("Usuario creado")
                    return redirect(url_for('usuarios'))

            return render_template("crear_usuario.html")
        except:
            flash("¡Ups! Ha ocurrido un error, intentelo de nuevo.")
            return render_template("crear_usuario.html")
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/buscar_vuelos', methods=['GET', 'POST'])
@login_required
def buscar_vuelos():
    return render_template('buscar_vuelos.html')


@app.route('/buscar_vuelos_ida_vuelta', methods=['GET', 'POST'])
@login_required
def buscar_vuelos_ida_vuelta():

    if request.method == 'POST':
        origen = request.form['origen']
        destino = request.form['destino']
        ida = request.form['ida']
        regreso = request.form['regreso']
        pasajero = request.form['pasajero']

        if not origen:
            flash('El campo de Origen no debe estar vacío')
        if not destino:
            flash('El campo de Destino no debe estar vacío')
        if not ida:
            flash('El campo de Fecha de ida no debe estar vacío')
        if not regreso:
            flash('El campo de Fecha de regreso no debe estar vacío')
        if not pasajero:
            flash('El campo de No de pasajeros no debe estar vacío')
        if origen and destino and ida and regreso and pasajero:

            vuelos = consultar_vuelos(origen, destino, ida, regreso)
            
            return render_template("buscar_vuelos_ida_vuelta.html", vuelos=vuelos, pasajero=pasajero)

    return render_template("buscar_vuelos_ida_vuelta.html")


@app.route('/buscar_vuelos_ida', methods=['GET', 'POST'])
@login_required
def buscar_vuelos_ida():

    if request.method == 'POST':
        origen = request.form['origen']
        destino = request.form['destino']
        ida = request.form['ida']
        pasajero = request.form['pasajero']

        if not origen:
            flash('El campo de Origen no debe estar vacío')
        if not destino:
            flash('El campo de Destino no debe estar vacío')
        if not ida:
            flash('El campo de Fecha de ida no debe estar vacío')
        if not pasajero:
            flash('El campo de No de pasajeros no debe estar vacío')
        if origen and destino and ida and pasajero:
            vuelos = consultar_vuelos_ida(origen, destino, ida)
            return render_template("buscar_vuelos_ida.html", vuelos=vuelos, pasajero=pasajero)

    return render_template("buscar_vuelos_ida.html")


@app.route('/calificar_vuelos', methods=['GET', 'POST'])
@login_required
def calificar_vuelos():
    if request.method == 'POST':
        ida = request.form['ida']
        regreso = request.form['regreso']

        if not ida:
            flash('El campo de Fecha de ida no debe estar vacío')
        if not regreso:
            flash('El campo de Fecha de regreso no debe estar vacío')
        if ida and regreso:
            db = get_db()
            vuelos = db.execute(
                'SELECT *  FROM vuelos WHERE fecha_ida=? AND fecha_vuelta=?', (ida, regreso)).fetchall()

            return render_template("calificar_vuelos.html", vuelos=vuelos)

    return render_template("calificar_vuelos.html")


@app.route('/reservas/<id_vuelo>/<pasajero>', methods=['GET', 'POST'])
@login_required
def reservas(id_vuelo, pasajero):

    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        identificacion = request.form['identificacion']
        email = request.form['email']

        if not nombre:
            flash('El campo nombre no debe estar vacío')
        if not apellido:
            flash('El campo apellido no debe estar vacío')
        if not identificacion:
            flash('El campo identificación no debe estar vacío')
        if not email:
            flash('El campo correo electrónico no debe estar vacío')

        else:
            db = get_db()
            user = consultar_usuarios(email,)

            session.clear()
            session['id_user'] = user[0]
            id_usuario = session.get('id_user')
            tipo = "ida y vuelta"
            db = get_db()
            vuelos = db.execute(
                'SELECT * FROM vuelos WHERE idvuelos = ?', (id_vuelo,)
            ).fetchone()

            reservar_vuelos(nombre, apellido, identificacion, email, id_usuario,
                            vuelos[1], vuelos[2], tipo, vuelos[8], vuelos[9], pasajero, vuelos[0], vuelos[4])

            flash('¡Reserva exitosa!')
            return render_template('reservas.html', vuelos=vuelos, id_vuelo=id_vuelo, pasajero=pasajero)

    vuelos = consultar_id_vuelo(id_vuelo,)
    return render_template('reservas.html', vuelos=vuelos, id_vuelo=id_vuelo, pasajero=pasajero)


@app.route('/reservas_ida/<id_vuelo>/<pasajero>', methods=['GET', 'POST'])
@login_required
def reservas_ida(id_vuelo, pasajero):

    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        identificacion = request.form['identificacion']
        email = request.form['email']

        if not nombre:
            flash('El campo nombre no debe estar vacío')
        if not apellido:
            flash('El campo apellido no debe estar vacío')
        if not identificacion:
            flash('El campo identificación no debe estar vacío')
        if not email:
            flash('El campo correo electrónico no debe estar vacío')

        else:
            db = get_db()
            user = consultar_usuarios(email,)
            
            session.clear()
            session['id_user'] = user[0]
            id_usuario = session.get('id_user')
            tipo = "ida"
            vuelos = db.execute(
                'SELECT * FROM vuelos WHERE idvuelos = ?', (id_vuelo,)
            ).fetchone()

            reservar_vuelos_ida(nombre, apellido, identificacion, email, id_usuario,
                                vuelos[1], vuelos[2], tipo, vuelos[8], pasajero, vuelos[0], vuelos[4])
            
            return render_template('reservas_ida.html', vuelos=vuelos, id_vuelo=id_vuelo, pasajero=pasajero)

    vuelos = consultar_id_vuelo(id_vuelo,)
    return render_template('reservas_ida.html', vuelos=vuelos, id_vuelo=id_vuelo, pasajero=pasajero)


@app.route('/comentarios', methods=['GET', 'POST'])
@login_required
def comentarios():
    db = get_db()
    
    comentarios = db.execute( 'SELECT * FROM comentarios',
                       ).fetchall()
    if request.method == 'POST':
        nombre = request.form['nombre']
        mensaje = request.form['mensaje']
        db.execute(
        'INSERT INTO comentarios (nombre,mensaje) VALUES (?,?);',
        (nombre,mensaje)
        )
        db.commit() 
        return redirect(url_for('comentarios'))
    return render_template('comentarios.html', comentarios=comentarios)

@app.route('/usuarios')
@login_required
def usuarios():
    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':
        usuarios = usuarios_consulta()
        return render_template('usuarios.html', usuarios=usuarios)
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/editar/<string:id>')
@login_required
def edit_usuario(id):
    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':
        db = get_db()
        cursor = db.execute(
            'SELECT *  FROM usuarios WHERE idusuarios=?',
            (id,)).fetchall()

        return render_template('editar_usuario.html', usuarios=cursor)
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/update/<string:id>', methods=['GET', 'POST'])
@login_required
def update_usuario(id):
    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':
        if request.method == 'POST':
            nombre = request.form['nombre']
            email = request.form['email']
            rol = request.form['rol']

            actualizar_usuarios(nombre, email, rol, id)

            flash("Contacto actualizado")
            return redirect(url_for('usuarios'))
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/eliminar/<string:id>')
@login_required
def eliminar_usuario(id):
    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':

        eliminar_usuarios(id)

        flash("Contacto eliminado")
        return redirect(url_for('usuarios'))
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/vuelos')
@login_required
def vuelos():
    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':
        vuelos = consulta_vuelos()
        return render_template('vuelos.html', vuelos=vuelos)
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/agregar_vuelo', methods=['GET', 'POST'])
@login_required
def agregar_vuelo():

    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':
        try:
            if request.method == 'POST':
                origen = request.form['origen']
                destino = request.form['destino']
                estado = request.form['estvuelo']
                numero_vuelo = request.form['numvuelo']
                puerta = request.form['puerta']
                hora_salida = request.form['horasalida']
                hora_llegada = request.form['horallegada']
                fecha_salida = request.form['fechasalida']
                fecha_vuelta = request.form['fechavuelta']
                piloto = request.form['pilotoasig']
                avion_asig = request.form['avionasig']
                capacidad = request.form['capvuelo']

                error = None
                if error is not None:
                    return render_template("agregar_vuelo.html")
                else:
                    agregar_vuelos(origen, destino, estado, numero_vuelo, puerta, hora_salida,
                                   hora_llegada, fecha_salida, fecha_vuelta, piloto, avion_asig, capacidad)
                    flash("Vuelo agregado")
                    return redirect(url_for('vuelos'))

            return render_template('agregar_vuelo.html')
        except:
            flash("¡Ups! Ha ocurrido un error, intentelo de nuevo.")
            return redirect(url_for('vuelos'))
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/modificar_vuelos/<string:id>')
@login_required
def edit_vuelos(id):
    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':
        db = get_db()
        cursor = db.execute(
            'SELECT *  FROM vuelos WHERE idvuelos=?',
            (id,)).fetchall()

        return render_template('modificar_vuelos.html', vuelos=cursor)
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/update_vuelo/<string:id>', methods=['GET', 'POST'])
@login_required
def update_vuelo(id):
    
    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':
        if request.method == 'POST':
            nom_cookie=request.cookies.get('username', 'email')
            origen = request.form['origen']
            destino = request.form['destino']
            estado = request.form['estado']
            vuelo = request.form['numero_vuelo']
            gate = request.form['gate']
            hora_salida = request.form['hora_salida']
            hora_llegada = request.form['hora_llegada']
            fecha_ida = request.form['fecha_ida']
            fecha_vuelta = request.form['fecha_vuelta']
            piloto = request.form['piloto']
            avion = request.form['avion']
            capacidad = request.form['capacidad']

            actualizar_vuelos(origen, destino, estado, vuelo, gate, hora_salida,
                              hora_llegada, fecha_ida, fecha_vuelta, piloto, avion, capacidad, id)

            flash("{} Vuelo se ha actualizado".format(nom_cookie))
            return redirect(url_for('vuelos'))
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/eliminar_vuelos/<string:id>')
@login_required
def eliminar_vuelo(id):
    rol_usuario = session.get('rol')
    if rol_usuario == 'adm':

        eliminar_vuelos(id,)
        nom_cookie=request.cookies.get('username', 'email')
        flash("{} El Vuelo ha sido eliminado".format(nom_cookie))
        return redirect(url_for('vuelos'))
    else:
        return redirect(url_for('acceso_denegado'))


@app.route('/inicio_usuario')
@login_required
def inicio_usuario():

    id = session.get('id_user')
    reserva = consultar_reservas(id,)
    return render_template('inicio_usuario.html', reserva=reserva)


@app.route('/piloto')
@login_required
def piloto():
    
    id = session.get('id_user')
    pilotos = consultar_piloto_vuelo(id)
    user_piloto = consultar_usuario_id(id)
    return render_template('piloto.html', pilotos=pilotos, user_piloto=user_piloto)


@app.route('/acceso_denegado')
def acceso_denegado():
    return render_template('acceso_denegado.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    resp = make_response(render_template('error.html'), 404)
    resp.headers['X-Something'] = 'A value'
    return resp




if __name__ == '__main__':
    app.run(debug=True, port=5000)
