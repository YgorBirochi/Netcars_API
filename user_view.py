from flask import Flask, jsonify, request
from main import app, con
import re
from flask_bcrypt import generate_password_hash

@app.route('/user', methods=['GET'])
def get_user():
    cursor = con.cursor()

    cursor.execute('SELECT ID_USUARIO, NOME, EMAIL, SENHA FROM USUARIOS')

    resultado = cursor.fetchall()

    user_dic = []
    for user in resultado:
        user_dic.append({
            'id_usuario': user[0],
            'nome': user[1],
            'email': user[2],
            'senha': user[3]
        })

    cursor.close()

    return jsonify({'usuarios': user_dic}), 200