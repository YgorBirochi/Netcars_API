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
            return jsonify({'manutencao': []}), 200

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

        # Inativa a manutenção
        cursor.execute('UPDATE MANUTENCAO SET ATIVO = FALSE WHERE ID_MANUTENCAO = ?', (id,))

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
        # Verificar existência da manutenção
        cursor.execute('SELECT 1 FROM MANUTENCAO WHERE ID_MANUTENCAO = ?', (id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Manutenção não encontrada.'}), 400

        # Buscar serviços com JOIN e ordenação
        cursor.execute('''
                SELECT 
                    MS.ID_SERVICOS, 
                    MS.QUANTIDADE,
                    MS.VALOR_TOTAL_ITEM,
                    S.DESCRICAO,
                    S.VALOR
                FROM MANUTENCAO_SERVICOS MS
                JOIN SERVICOS S ON MS.ID_SERVICOS = S.ID_SERVICOS
                WHERE MS.ID_MANUTENCAO = ?
                ORDER BY MS.ID_SERVICOS  -- Garante ordem consistente
            ''', (id,))

        servicos = [
            {
                "id_servicos": row[0],
                "quantidade": row[1],
                "valor_total_item": row[2],
                "descricao": row[3],
                "valor_unitario": row[4]
            }
            for row in cursor.fetchall()
        ]

        return jsonify({'servicos': servicos}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()

@app.route('/manutencao_servicos', methods=['POST'])
def add_manutencao_servico():
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
    id_manutencao = data.get('id_manutencao')
    id_servico = data.get('id_servico')
    quantidade = data.get('quantidade', 1)  # Default é 1 se não for especificado

    if not id_manutencao or not id_servico:
        return jsonify({'error': 'Dados incompletos. ID da manutenção e ID do serviço são obrigatórios'}), 400

    try:
        # Verificar se a manutenção existe
        cursor.execute('SELECT 1 FROM MANUTENCAO WHERE ID_MANUTENCAO = ? AND ATIVO IS TRUE', (id_manutencao,))
        if not cursor.fetchone():
            return jsonify({'error': 'Manutenção não encontrada ou inativa'}), 404

        # Verificar se o serviço existe
        cursor.execute('SELECT VALOR FROM SERVICOS WHERE ID_SERVICOS = ? AND ATIVO IS TRUE', (id_servico,))
        servico = cursor.fetchone()
        if not servico:
            return jsonify({'error': 'Serviço não encontrado ou inativo'}), 404

        valor_unitario = servico[0]
        valor_total_item = valor_unitario * quantidade

        # Verificar se este serviço já está associado a esta manutenção
        cursor.execute('SELECT 1 FROM MANUTENCAO_SERVICOS WHERE ID_MANUTENCAO = ? AND ID_SERVICOS = ?',
                       (id_manutencao, id_servico))
        if cursor.fetchone():
            return jsonify({'error': 'Este serviço já está associado a esta manutenção'}), 400

        # Inserir na tabela de associação
        cursor.execute('''
            INSERT INTO MANUTENCAO_SERVICOS 
            (ID_MANUTENCAO, ID_SERVICOS, QUANTIDADE, VALOR_TOTAL_ITEM)
            VALUES (?, ?, ?, ?)
            RETURNING ID_MANUTENCAO_SERVICOS
        ''', (id_manutencao, id_servico, quantidade, valor_total_item))

        id_manutencao_servico = cursor.fetchone()[0]

        con.commit()

        return jsonify({
            'success': 'Serviço adicionado à manutenção com sucesso',
            'id_manutencao_servico': id_manutencao_servico
        }), 201

    except Exception as e:
        con.rollback()
        return jsonify({'error': f'Erro ao adicionar serviço à manutenção: {str(e)}'}), 500
    finally:
        cursor.close()


@app.route('/manutencao_servicos/<int:id_manutencao>/<int:id_servico>', methods=['DELETE'])
def remove_manutencao_servico(id_manutencao, id_servico):
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
        # Verificar se a associação existe
        cursor.execute('''
            SELECT 1 FROM MANUTENCAO_SERVICOS 
            WHERE ID_MANUTENCAO = ? AND ID_SERVICOS = ?
        ''', (id_manutencao, id_servico))

        if not cursor.fetchone():
            return jsonify({'error': 'Associação não encontrada'}), 404

        # Remover a associação
        cursor.execute('''
            DELETE FROM MANUTENCAO_SERVICOS 
            WHERE ID_MANUTENCAO = ? AND ID_SERVICOS = ?
        ''', (id_manutencao, id_servico))

        con.commit()

        return jsonify({
            'success': 'Serviço removido da manutenção com sucesso'
        }), 200

    except Exception as e:
        con.rollback()
        return jsonify({'error': f'Erro ao remover serviço da manutenção: {str(e)}'}), 500
    finally:
        cursor.close()


@app.route('/manutencao_servicos/<int:id_manutencao>', methods=['PUT'])
def update_manutencao_servico(id_manutencao):
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
    id_servico = data.get('id_servico')
    quantidade = data.get('quantidade')

    if not id_servico or not quantidade:
        return jsonify({'error': 'Dados incompletos. ID do serviço e quantidade são obrigatórios'}), 400

    data = request.get_json()
    id_servico = data.get('id_servico')
    quantidade = data.get('quantidade')

    # Validação de tipo da quantidade
    try:
        quantidade = int(quantidade)  # Força conversão para inteiro
    except (ValueError, TypeError):
        return jsonify({'error': 'Quantidade deve ser um número inteiro'}), 400

    try:
        # Buscar valor unitário como Decimal
        cursor.execute('SELECT VALOR FROM SERVICOS WHERE ID_SERVICOS = ?', (id_servico,))
        servico = cursor.fetchone()
        if not servico:
            return jsonify({'error': 'Serviço não encontrado'}), 404

        valor_unitario = float(servico[0])  # Converte Decimal para float
        valor_total_item = valor_unitario * quantidade

        # Atualizar no banco
        cursor.execute('''
                UPDATE MANUTENCAO_SERVICOS 
                SET QUANTIDADE = ?, VALOR_TOTAL_ITEM = ?
                WHERE ID_MANUTENCAO = ? AND ID_SERVICOS = ?
            ''', (quantidade, valor_total_item, id_manutencao, id_servico))

        con.commit()

        return jsonify({'success': 'Serviço atualizado!'}), 200

    except Exception as e:
        con.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500
    finally:
        cursor.close()


@app.route('/manutencao_servicos/<int:id_manutencao>/<int:id_servico>', methods=['GET'])
def get_servico_manutencao(id_manutencao, id_servico):
    try:
        cursor = con.cursor()
        cursor.execute('''
            SELECT 
                MS.ID_SERVICOS,
                MS.QUANTIDADE,
                MS.VALOR_TOTAL_ITEM,
                S.DESCRICAO,
                S.VALOR
            FROM MANUTENCAO_SERVICOS MS
            JOIN SERVICOS S ON MS.ID_SERVICOS = S.ID_SERVICOS
            WHERE MS.ID_MANUTENCAO = ? AND MS.ID_SERVICOS = ?
        ''', (id_manutencao, id_servico))

        servico = cursor.fetchone()

        if not servico:
            return jsonify({'error': 'Serviço não encontrado na manutenção'}), 404

        return jsonify({
            'id_servicos': servico[0],
            'quantidade': servico[1],
            'valor_total_item': float(servico[2]),
            'descricao': servico[3],
            'valor_unitario': float(servico[4])
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()


@app.route('/manutencao_servicos/<int:id_manutencao>/<int:id_servico>', methods=['PUT'])
def update_manutencao_servico_v2(id_manutencao, id_servico):
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
    novo_id_servico = data.get('novo_id_servico')
    quantidade = data.get('quantidade')

    # Validações básicas
    if novo_id_servico is None or quantidade is None:
        return jsonify({'error': 'Dados incompletos'}), 400

    try:
        # Converter para inteiros
        novo_id_servico = int(novo_id_servico)
        quantidade = int(quantidade)
    except (ValueError, TypeError):
        return jsonify({'error': 'IDs e quantidade devem ser números inteiros'}), 400

    if quantidade <= 0:
        return jsonify({'error': 'Quantidade inválida'}), 400

    try:
        # Verificar existência do novo serviço
        cursor.execute('SELECT VALOR FROM SERVICOS WHERE ID_SERVICOS = ?', (novo_id_servico,))
        servico = cursor.fetchone()
        if not servico:
            return jsonify({'error': 'Novo serviço não encontrado'}), 404

        valor_unitario = servico[0]
        valor_total_item = valor_unitario * quantidade

        # Verificar duplicatas apenas se for um serviço diferente
        if novo_id_servico != id_servico:
            # Modificado: Ignora o registro atual na verificação
            cursor.execute('''
                    SELECT 1 FROM MANUTENCAO_SERVICOS 
                    WHERE ID_MANUTENCAO = ? 
                    AND ID_SERVICOS = ? 
                    AND ID_SERVICOS != ?  -- Exclui o registro atual da verificação
                ''', (id_manutencao, novo_id_servico, id_servico))  # Usar id_servico original

            if cursor.fetchone():
                return jsonify({'error': 'Este serviço já está na manutenção'}), 400

        # Atualizar registro (mesmo código)
        cursor.execute('''
                UPDATE MANUTENCAO_SERVICOS 
                SET ID_SERVICOS = ?, 
                    QUANTIDADE = ?, 
                    VALOR_TOTAL_ITEM = ?
                WHERE ID_MANUTENCAO = ? 
                AND ID_SERVICOS = ?
            ''', (novo_id_servico, quantidade, valor_total_item, id_manutencao, id_servico))

        con.commit()

        return jsonify({'success': 'Serviço atualizado com sucesso!'}), 200

    except Exception as e:
        con.rollback()
        print(f"Erro interno: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500
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

    # Validações dos campos obrigatórios
    if not descricao:
        return jsonify({'error': 'Descrição é obrigatória'}), 400

    if valor is None:
        return jsonify({'error': 'Valor é obrigatório'}), 400

    # Verificar que valor é um número válido
    try:
        valor = float(valor)
        if valor <= 0:
            return jsonify({'error': 'Valor deve ser maior que zero'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Valor inválido. Deve ser um número'}), 400

    try:
        # Inserir o novo serviço no banco de dados
        cursor.execute('INSERT INTO SERVICOS (DESCRICAO, VALOR, ATIVO) VALUES (?, ?, TRUE) RETURNING ID_SERVICOS',
                       (descricao, valor))
        id_servico = cursor.fetchone()[0]
        con.commit()

        return jsonify({
            'success': 'Serviço cadastrado com sucesso',
            'id_servico': id_servico
        }), 201
    except Exception as e:
        con.rollback()
        return jsonify({'error': f'Erro ao cadastrar serviço: {str(e)}'}), 500
    finally:
        cursor.close()


@app.route('/servicos/<int:id_servicos>', methods=['PUT'])
def put_servico(id_servicos):
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

    cursor = None  # Inicializa como None para tratamento seguro
    try:
        cursor = con.cursor()

        # Verifica permissão do usuário
        cursor.execute('SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
        user_type = cursor.fetchone()[0]
        if user_type not in [1, 2]:
            return jsonify({'error': 'Acesso restrito a administradores'}), 403

        # Obtém dados do JSON
        data = request.get_json()
        descricao = data.get('descricao')
        valor = data.get('valor')

        # Validação dos campos
        if not descricao or valor is None:
            return jsonify({'error': 'Dados incompletos.'}), 400

        # Verifica existência do serviço
        cursor.execute('SELECT 1 FROM SERVICOS WHERE id_servicos = ?', (id_servicos,))
        if not cursor.fetchone():
            return jsonify({'error': 'Serviço não encontrado.'}), 404

        # Atualiza o serviço
        cursor.execute('''
            UPDATE SERVICOS 
            SET DESCRICAO = ?, VALOR = ?
            WHERE id_servicos = ?
        ''', (descricao, valor, id_servicos))

        # Verifica se há manutenção associada (evita None[0])
        cursor.execute('''
            SELECT ID_MANUTENCAO 
            FROM MANUTENCAO_SERVICOS 
            WHERE ID_SERVICOS = ?
        ''', (id_servicos,))
        resultado = cursor.fetchone()

        con.commit()
        return jsonify({'success': 'Serviço atualizado com sucesso.'}), 200

    except Exception as e:
        con.rollback()  # Reverte em caso de erro
        return jsonify({'error': str(e)}), 500  # Erro genérico do servidor

    finally:
        if cursor:  # Fecha cursor apenas se existir
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

    cursor = None  # Inicialize como None para tratamento seguro
    try:
        cursor = con.cursor()

        # Verifica permissão do usuário
        cursor.execute('SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
        user_type = cursor.fetchone()[0]
        if user_type not in [1, 2]:
            return jsonify({'error': 'Acesso restrito a administradores'}), 403

        # Verifica existência do serviço
        cursor.execute('SELECT 1 FROM SERVICOS WHERE id_servicos = ?', (id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Serviço não encontrado'}), 404

        # Inativa o serviço (não exclui)
        cursor.execute('''
            UPDATE SERVICOS 
            SET ATIVO = FALSE 
            WHERE id_servicos = ?
        ''', (id,))

        # Verifica se há manutenção associada
        cursor.execute('''
            SELECT ID_MANUTENCAO 
            FROM MANUTENCAO_SERVICOS 
            WHERE ID_SERVICOS = ?
        ''', (id,))
        resultado = cursor.fetchone()

        con.commit()
        return jsonify({'success': 'Serviço inativado com sucesso.'}), 200

    except Exception as e:
        con.rollback()
        return jsonify({'error': str(e)}), 500  # Erro genérico do servidor

    finally:
        if cursor:  # Fecha o cursor apenas se existir
            cursor.close()
