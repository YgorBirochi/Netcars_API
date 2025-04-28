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
            'SELECT ID_MANUTENCAO, ID_VEICULO, TIPO_VEICULO, DATA_MANUTENCAO, OBSERVACAO, VALOR_TOTAL FROM MANUTENCAO WHERE ATIVO IS TRUE')

        resposta = cursor.fetchall()
        if not resposta:
            return jsonify({'error': 'Nenhuma manutenção encontrada.'}), 400

        manutencoes = []

        for manutencao in resposta:
            manutencoes.append({
                'id_manutencao': manutencao[0],
                'id_veiculo': manutencao[1],
                'tipo_veiculo': manutencao[2],
                'data_manutencao': manutencao[3],
                'observacao': manutencao[4],
                'valor_total': manutencao[5]
            })

        return jsonify({
            'manutencoes': manutencoes
        }), 200
    except Exception as e:
        return jsonify({
            'error': e
        }), 400
    finally:
        cursor.close()

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

        cursor.execute('''
            SELECT ID_MANUTENCAO, ID_VEICULO, TIPO_VEICULO, DATA_MANUTENCAO, OBSERVACAO, VALOR_TOTAL 
            FROM MANUTENCAO WHERE ID_MANUTENCAO = ? AND ATIVO IS TRUE
        ''', (id,))

        manutencao = cursor.fetchone()

        if not manutencao:
            return jsonify({'error': 'Manutenção não encontrada.'}), 400

        data = {
            'id_manutencao': manutencao[0],
            'id_veiculo': manutencao[1],
            'tipo_veiculo': manutencao[2],
            'data_manutencao': manutencao[3],
            'observacao': manutencao[4],
            'valor_total': manutencao[5]
        }

        return jsonify({
            'manutencao': data
        }), 200
    except Exception as e:
        return jsonify({
            'error': e
        }), 400
    finally:
        cursor.close()

@app.route('/manutencao_veic/<int:id_veic>/<tipo_veic>', methods=['GET'])
def get_manutencao_id_veic(id_veic, tipo_veic):
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

        if tipo_veic == 'carro':
            cursor.execute('''
            SELECT ID_MANUTENCAO, ID_VEICULO, TIPO_VEICULO, DATA_MANUTENCAO, OBSERVACAO, VALOR_TOTAL 
            FROM MANUTENCAO WHERE ID_VEICULO = ? AND TIPO_VEICULO = 1 AND ATIVO IS TRUE ORDER BY DATA_MANUTENCAO ASC''',(id_veic,))
        else:
            cursor.execute('''
            SELECT ID_MANUTENCAO, ID_VEICULO, TIPO_VEICULO, DATA_MANUTENCAO, OBSERVACAO, VALOR_TOTAL 
            FROM MANUTENCAO WHERE ID_VEICULO = ? AND TIPO_VEICULO = 2 AND ATIVO IS TRUE ORDER BY DATA_MANUTENCAO ASC''', (id_veic,))

        manutencoes = cursor.fetchall()

        if not manutencoes or len(manutencoes) <= 0:
            return jsonify({'error': 'Manutenção não encontrada.'}), 400

        data = []

        for manutencao in manutencoes:
            data.append({
                'id_manutencao': manutencao[0],
                'id_veiculo': manutencao[1],
                'tipo_veiculo': manutencao[2],
                'data_manutencao': manutencao[3],
                'observacao': manutencao[4],
                'valor_total': manutencao[5]
            })

        return jsonify({
            'manutencao': data
        }), 200
    except Exception as e:
        return jsonify({
            'error': e
        }), 400
    finally:
        cursor.close()

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
    tipo_veic = 1 if data.get('tipo_veic') == 'carro' else 2
    data_manutencao = data.get('data')
    observacao = data.get('observacao')

    if not id_veic or not tipo_veic or not data_manutencao or not observacao:
        return jsonify({
            'error': 'Dados incompletos.'
        }), 400

    cursor = con.cursor()

    if tipo_veic == 1:
        cursor.execute('SELECT 1 FROM CARROS WHERE ID_CARRO = ?',(id_veic,))
        if not cursor.fetchone():
            return jsonify({'error': 'Veículo não encontrado.'}), 400
    else:
        cursor.execute('SELECT 1 FROM MOTOS WHERE ID_MOTO = ?', (id_veic,))
        if not cursor.fetchone():
            return jsonify({'error': 'Veículo não encontrado.'}), 400

    cursor.execute('''
            INSERT INTO MANUTENCAO 
            (ID_VEICULO, TIPO_VEICULO, DATA_MANUTENCAO, OBSERVACAO, ATIVO, VALOR_TOTAL)
            VALUES
            (?, ?, ?, ?, TRUE, 0)
            RETURNING ID_MANUTENCAO
        ''', (id_veic, tipo_veic, data_manutencao, observacao))

    id_manutencao = cursor.fetchone()[0]

    con.commit()
    cursor.close()

    return jsonify({
        'success': 'Manutenção cadastrada com sucesso.',
        'id_manutencao': id_manutencao
    }), 200

@app.route('/manutencao/<int:id_veic>', methods=['PUT'])
def put_manutencao(id_veic):
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

    tipo_veic = 1 if data.get('tipo_veic') == 'carro' else 2
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
        cursor.execute('SELECT 1 FROM MANUTENCAO WHERE ID_MANUTENCAO = ?', (id,))

        if cursor.fetchone() is None:
            return jsonify({'error': 'Manutenção não encontrada'}), 404

        cursor.execute('UPDATE MANUTENCAO SET ATIVO = FALSE WHERE ID_MANUTENCAO = ?', (id,))

        cursor.execute('SELECT ID_SERVICOS FROM MANUTENCAO_SERVICOS WHERE ID_MANUTENCAO = ?', (id,))
        ids_servicos = [row[0] for row in cursor.fetchall()]

        if ids_servicos:
            for id_servico in ids_servicos:
                cursor.execute('UPDATE SERVICOS SET ATIVO = FALSE WHERE ID_SERVICOS = ?', (id_servico, ))

        con.commit()
        return jsonify({'success': 'Manutenção excluída com sucesso.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()

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
        cursor.execute('SELECT id_servicos, DESCRICAO, VALOR FROM SERVICOS WHERE ATIVO IS TRUE')
        servicos = [
            {'id_servicos': s[0], 'descricao': s[1], 'valor': s[2]}
            for s in cursor.fetchall()
        ]
        return jsonify({'servicos': servicos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()

@app.route('/manutencao_servicos/<int:id>', methods=['GET'])
def get_manutencao_servicos(id):
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
        cursor.execute('SELECT 1 FROM MANUTENCAO WHERE ID_MANUTENCAO = ?', (id,))
        resposta = cursor.fetchone()
        if not resposta:
            return jsonify({'error': 'Manutenção não encontrada.'}), 400

        cursor.execute('SELECT ID_SERVICOS FROM MANUTENCAO_SERVICOS WHERE ID_MANUTENCAO = ?', (id,))
        resposta = cursor.fetchall()
        if not resposta or len(resposta) < 0:
            return jsonify({'servicos': []}), 200

        ids_servicos = [row[0] for row in resposta]

        servicos = []
        for id_serv in ids_servicos:
            cursor.execute('SELECT ID_SERVICOS, DESCRICAO, VALOR FROM SERVICOS WHERE id_servicos = ? AND ATIVO IS TRUE', (id_serv,))
            servico = cursor.fetchone()
            if servico:
                servicos.append({
                    "id_servicos": servico[0],
                    "descricao": servico[1],
                    "valor": servico[2]
                })

        return jsonify({
            'servicos': servicos
        }), 200
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
        cursor.execute('SELECT id_servicos, DESCRICAO, VALOR FROM SERVICOS WHERE id_servicos = ? AND ATIVO IS TRUE', (id,))
        servico = cursor.fetchone()
        if not servico:
            return jsonify({'error': 'Serviço não encontrado'}), 404

        return jsonify({
            'servico': {
                'id_servicos': servico[0],
                'descricao': servico[1],
                'valor': servico[2]
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()

# Função para atualizar o valor total
def atualizar_valor_total(id_manutencao):
    cursor = con.cursor()

    try:
        cursor.execute('''
                        SELECT ID_SERVICOS FROM MANUTENCAO_SERVICOS
                        WHERE ID_MANUTENCAO = ?
                    ''', (id_manutencao,))

        ids_servicos = [row[0] for row in cursor.fetchall()]

        valor_total = 0

        for id in ids_servicos:
            cursor.execute('''
                        SELECT VALOR FROM SERVICOS WHERE ATIVO IS TRUE AND ID_SERVICOS = ?
                        ''', (id,))
            valor = cursor.fetchone()

            if not valor or valor is None:
                continue

            valor_total += valor[0]

        cursor.execute('''
            UPDATE MANUTENCAO SET VALOR_TOTAL = ?
            WHERE ID_MANUTENCAO = ?
        ''', (valor_total, id_manutencao))
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
    id_manutencao = int(data.get('id_manutencao'))

    if not descricao or valor is None or not id_manutencao:
        return jsonify({'error': 'Dados incompletos.'}), 400

    if int(valor) <= 0:
        return jsonify({'error': 'Valor inválido.'}), 400

    cursor.execute('SELECT ID_MANUTENCAO FROM MANUTENCAO')
    ids_manutencao = [row[0] for row in cursor.fetchall()]

    if id_manutencao not in ids_manutencao:
        return jsonify({'error': 'Manutenção não encontrada.'}), 400

    try:
        cursor.execute('INSERT INTO SERVICOS (DESCRICAO, VALOR, ATIVO) VALUES (?, ?, TRUE) RETURNING ID_SERVICOS', (descricao, valor))
        id_servico = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO MANUTENCAO_SERVICOS
            (ID_MANUTENCAO, ID_SERVICOS)
            VALUES (?, ?)
        ''', (id_manutencao, id_servico))

        atualizar_valor_total(id_manutencao)

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

        cursor.execute('SELECT ID_MANUTENCAO FROM MANUTENCAO_SERVICOS WHERE ID_SERVICOS = ?', (id_servicos,))

        id_manutencao = cursor.fetchone()[0]

        # Atualizar o valor total
        atualizar_valor_total(id_manutencao)

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

        cursor.execute('UPDATE SERVICOS SET ATIVO = FALSE WHERE id_servicos = ?', (id,))

        cursor.execute('SELECT ID_MANUTENCAO FROM MANUTENCAO_SERVICOS WHERE ID_SERVICOS = ?', (id,))

        # Obtém o id da manutenção
        id_manutencao = cursor.fetchone()[0]

        # Atualiza o valor total
        atualizar_valor_total(id_manutencao)

        con.commit()
        return jsonify({'success': 'Serviço excluído com sucesso.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()