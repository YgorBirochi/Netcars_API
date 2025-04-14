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

@app.route('/servicos', methods=['GET'])
def get_servicos():
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
        cursor.execute('SELECT id_servicos, DESCRICAO, VALOR FROM SERVICOS')
        servicos = [
            {'id_servicos': s[0], 'descricao': s[1], 'valor': s[2]}
            for s in cursor.fetchall()
        ]
        return jsonify({'servicos': servicos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()

@app.route('/servicos/<int:id>', methods=['GET'])
def get_servico_id(id):
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
        cursor.execute('SELECT id_servicos, DESCRICAO, VALOR FROM SERVICOS WHERE id_servicos = ?', (id,))
        servico = cursor.fetchone()
        if not servico:
            return jsonify({'error': 'Serviço não encontrado'}), 404

        return jsonify({
            'servico': {
                'id_servicoss': servico[0],
                'descricao': servico[1],
                'valor': servico[2]
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()

@app.route('/servicos', methods=['POST'])
def post_servico():
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
    descricao = data.get('descricao')
    valor = data.get('valor')
    id_manutencao = data.get('id_manutencao')

    cursor.execute('SELECT ID_MANUTENCAO FROM MANUTENCAO')
    ids_manutencao = [row[0] for row in cursor.fetchall()]
    if id_manutencao not in ids_manutencao:
        return jsonify({'error': 'Manutenção não encontrada.'}), 400

    if not descricao or valor is None or not id_manutencao:
        return jsonify({'error': 'Dados incompletos.'}), 400

    try:
        cursor.execute('INSERT INTO SERVICOS (DESCRICAO, VALOR) VALUES (?, ?) RETURNING ID_SERVICOS', (descricao, valor))
        id_servico = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO MANUTENCAO_SERVICOS
            (ID_MANUTENCAO, ID_SERVICOS)
            VALUES (?, ?)
        ''', (id_manutencao, id_servico))

        con.commit()

        return jsonify({'success': 'Serviço cadastrado com sucesso.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()

@app.route('/servicos', methods=['PUT'])
def put_servico():
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
    id_servicos = data.get('id_servicos')
    descricao = data.get('descricao')
    valor = data.get('valor')

    if not id_servicos or not descricao or valor is None:
        return jsonify({'error': 'Dados incompletos.'}), 400

    try:
        cursor.execute('SELECT 1 FROM SERVICOS WHERE id_servicos = ?', (id_servicos,))
        if cursor.fetchone() is None:
            return jsonify({'error': 'Serviço não encontrado.'}), 404

        cursor.execute('''
            UPDATE SERVICOS SET DESCRICAO = ?, VALOR = ?
            WHERE id_servicos = ?
        ''', (descricao, valor, id_servicos))
        con.commit()
        return jsonify({'success': 'Serviço atualizado com sucesso.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()

@app.route('/servicos/<int:id>', methods=['DELETE'])
def delete_servico(id):
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
        cursor.execute('SELECT 1 FROM SERVICOS WHERE id_servicos = ?', (id,))
        if cursor.fetchone() is None:
            return jsonify({'error': 'Serviço não encontrado'}), 404

        cursor.execute('DELETE FROM SERVICOS WHERE id_servicos = ?', (id,))
        con.commit()
        return jsonify({'success': 'Serviço excluído com sucesso.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()