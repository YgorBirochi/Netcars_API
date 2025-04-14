from flask import Flask, jsonify, request
from main import app, con, senha_secreta
import re
from flask_bcrypt import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token
@app.route('/manutencao', methods=['GET'])
def get_manutencao():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)
    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    cursor = con.cursor()

    cursor.execute('SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
    user_type = cursor.fetchone()[0]
    if user_type not in [1, 2]:
        return jsonify({'error': 'Acesso restrito a administradores'}), 403

    try:
        cursor = con.cursor()

        cursor.execute(
            'SELECT ID_MANUTENCAO, ID_VEICULO, TIPO_VEICULO, DATA_MANUTENCAO, OBSERVACAO, VALOR_TOTAL FROM MANUTENCAO')

        manutencoes = []

        for manutencao in cursor.fetchall():
            manutencoes.append(manutencao)

        cursor.close()
    except Exception as e:
        return jsonify({
            'error': e
        }), 400
    finally:
        return jsonify({
            'manutencoes': manutencoes
        }), 200

@app.route('/manutencao/<int:id>', methods=['GET'])
def get_manutencao_id(id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)
    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    cursor = con.cursor()

    cursor.execute('SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
    user_type = cursor.fetchone()[0]
    if user_type not in [1, 2]:
        return jsonify({'error': 'Acesso restrito a administradores'}), 403

    try:
        cursor = con.cursor()

        cursor.execute(
            'SELECT ID_MANUTENCAO, ID_VEICULO, TIPO_VEICULO, DATA_MANUTENCAO, OBSERVACAO, VALOR_TOTAL FROM MANUTENCAO WHERE ID_MANUTENCAO = ?', (id,))

        manutencao = cursor.fetchone()

        data = {
            'id_manutencao': manutencao[0],
            'id_veiculo': manutencao[1],
            'tipo_veiculo': manutencao[2],
            'data_manutencao': manutencao[3],
            'observacao': manutencao[4],
            'valor_total': manutencao[5]
        }

        cursor.close()

        return jsonify({
            'manutencao': data
        }), 200
    except Exception as e:
        return jsonify({
            'error': e
        }), 400

@app.route('/manutencao', methods=['POST'])
def post_manutencao():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)

    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    cursor = con.cursor()

    cursor.execute('SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
    user_type = cursor.fetchone()[0]
    if user_type not in [1, 2]:
        return jsonify({'error': 'Acesso restrito a administradores'}), 403

    data = request.get_json()

    id_veic = data.get('id_veic')
    tipo_veic = data.get('tipo_veic')
    data_manutencao = data.get('data')
    observacao = data.get('observacao')

    if not id_veic or not tipo_veic or not data or not observacao:
        return jsonify({
            'error': 'Dados incompletos.'
        }), 400

    cursor = con.cursor()

    cursor.execute('''
            INSERT INTO MANUTENCAO 
            (ID_VEICULO, TIPO_VEICULO, DATA_MANUTENCAO, OBSERVACAO)
            VALUES
            (?, ?, ?, ?)
        ''', (id_veic, tipo_veic, data_manutencao, observacao))

    con.commit()
    cursor.close()

    return jsonify({
        'success': 'Manutenção cadastrada com sucesso.'
    }), 200

@app.route('/manutencao', methods=['PUT'])
def put_manutencao():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)

    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    cursor = con.cursor()
    cursor.execute('SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
    user_type = cursor.fetchone()[0]
    if user_type not in [1, 2]:
        return jsonify({'error': 'Acesso restrito a administradores'}), 403

    data = request.get_json()

    id_veic = data.get('id_veic')
    tipo_veic = data.get('tipo_veic')
    data_manutencao = data.get('data')
    observacao = data.get('observacao')
    id_manutencao = data.get('id_manutencao')

    if not id_veic or not tipo_veic or not data_manutencao or not observacao or not id_manutencao:
        return jsonify({'error': 'Dados incompletos.'}), 400

    # Verifica se manutenção existe
    cursor.execute('SELECT 1 FROM MANUTENCAO WHERE ID_MANUTENCAO = ?', (id_manutencao,))
    if cursor.fetchone() is None:
        return jsonify({'error': 'Manutenção não encontrada.'}), 404

    cursor.execute('''
        UPDATE MANUTENCAO 
        SET ID_VEICULO = ?, 
            TIPO_VEICULO = ?, 
            DATA_MANUTENCAO = ?, 
            OBSERVACAO = ?
        WHERE ID_MANUTENCAO = ?
    ''', (id_veic, tipo_veic, data_manutencao, observacao, id_manutencao))

    con.commit()
    cursor.close()

    return jsonify({'success': 'Dados atualizados com sucesso.'}), 200

@app.route('/manutencao/<int:id>', methods=['DELETE'])
def delete_manutencao(id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)

    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    cursor = con.cursor()
    cursor.execute('SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
    user_type = cursor.fetchone()[0]
    if user_type not in [1, 2]:
        return jsonify({'error': 'Acesso restrito a administradores'}), 403

    try:
        cursor.execute('SELECT * FROM MANUTENCAO WHERE ID_MANUTENCAO = ?', (id,))
        if cursor.fetchone() is None:
            return jsonify({'error': 'Manutenção não encontrada'}), 404

        cursor.execute('DELETE FROM MANUTENCAO WHERE ID_MANUTENCAO = ?', (id,))
        con.commit()
        return jsonify({'success': 'Manutenção excluída com sucesso.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()