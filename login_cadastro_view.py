from flask import Flask, jsonify, request
from main import app, con, senha_secreta
from datetime import datetime, timedelta
from flask_bcrypt import generate_password_hash, check_password_hash
import jwt
import re

def generate_token(user_id, email):
    payload = {'id_usuario': user_id, 'email': email}
    token = jwt.encode(payload, senha_secreta, algorithm='HS256')
    return token

def validar_senha(senha):
    if len(senha) < 8:
        return "A senha deve ter pelo menos 8 caracteres."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
        return "A senha deve conter pelo menos um símbolo especial (!@#$%^&*...)."

    if not re.search(r"[A-Z]", senha):
        return "A senha deve conter pelo menos uma letra maiúscula."

    return True

def formatarNome(nome):
    partes = nome.split()
    partes_formatadas = [p.lower().capitalize() for p in partes]
    return " ".join(partes_formatadas)

@app.route('/manutencao', methods=['GET'])
def get_manu():
    cursor = con.cursor()

    cursor.execute('SELECT ID_MANUTENCAO, TIPO_VEICULO, DATA_MANUTENCAO, SITUACAO, VALOR_TOTAL FROM MANUTENCAO ')
    resultado = cursor.fetchall()

    manu_dic = []
    for manu in resultado:
        manu_dic.append({
            'id_manutencao': manu[0],
            '': manu[1],
            'valor_total': manu[2],
            'situacao': manu[3],
            'data_manutencao': manu[4],
        })

    cursor.close()

    return jsonify({'manutencao': manu_dic}), 200

@app.route('/cadastro', methods=['GET'])
def get_user():
    cursor = con.cursor()

    cursor.execute('SELECT ID_USUARIO, NOME_COMPLETO, EMAIL, TELEFONE, ATIVO, TIPO_USUARIO FROM USUARIO')

    resultado = cursor.fetchall()

    user_dic = []
    for user in resultado:
        user_dic.append({
            'id_usuario': user[0],
            'nome_completo': user[1],
            'email': user[2],
            'telefone': user[3],
            'ativo': user[4],
            'tipo_usuario': user[5]
        })

    cursor.close()

    return jsonify({'usuarios': user_dic}), 200

@app.route('/get_user_filtro', methods=['POST'])
def get_user_filtro():
    data = request.get_json()

    nomeLike = data.get('nome-like', '').lower()
    ativo = data.get('ativo')
    tipo_usuario = data.get('tipo_usuario')

    query = '''
        SELECT ID_USUARIO, NOME_COMPLETO, EMAIL, TELEFONE, ATIVO, TIPO_USUARIO 
        FROM USUARIO
    '''
    conditions = []
    parameters = []

    # Se for informado um nome/email, adiciona a condição com o LIKE
    if nomeLike:
        conditions.append('(NOME_COMPLETO LIKE ? OR EMAIL LIKE ?)')
        nomeLike = f"%{nomeLike}%"
        parameters.extend([nomeLike, nomeLike])

    # Se o filtro "ativo" for informado
    if ativo is not None and ativo != '':
        conditions.append('ATIVO = ?')
        parameters.append(ativo)

    # Se o filtro "tipo_usuario" for informado
    if tipo_usuario is not None and tipo_usuario != '':
        conditions.append('TIPO_USUARIO = ?')
        parameters.append(tipo_usuario)

    # Se houver condições, junta-as na query
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor = con.cursor()
    cursor.execute(query, tuple(parameters))
    resultado = cursor.fetchall()

    user_dic = []
    for user in resultado:
        user_dic.append({
            'id_usuario': user[0],
            'nome_completo': user[1],
            'email': user[2],
            'telefone': user[3],
            'ativo': user[4],
            'tipo_usuario': user[5]
        })

    cursor.close()
    return jsonify({'usuarios': user_dic}), 200

@app.route('/cadastro', methods=['POST'])
def create_user():
    data = request.get_json()
    nome = data.get('nome_completo')
    email = data.get('email')
    senha = data.get('senha_hash')
    tipo_usuario = data.get('tipo_usuario')

    nome = formatarNome(nome)

    cursor = con.cursor()
    cursor.execute("SELECT 1 FROM USUARIO WHERE email = ?", (email,))

    if cursor.fetchone():
        return jsonify({'error': 'Email já cadastrado'}), 400

    senha_check = validar_senha(senha)
    if senha_check is not True:
        return jsonify({'error': senha_check}), 400

    senha_hash = generate_password_hash(senha).decode('utf-8')

    cursor.execute("INSERT INTO USUARIO (nome_completo, email, senha_hash, ativo, tipo_usuario) VALUES (?, ?, ?, 1, ?) RETURNING ID_USUARIO", (nome, email, senha_hash, tipo_usuario))

    id_usuario = cursor.fetchone()[0]

    con.commit()

    cursor.close()
    token = generate_token(id_usuario, email)

    return jsonify({
        'success': "Email cadastrado com sucesso!",
        'dados': {
            'nome_completo': nome,
            'email': email,
            'id_usuario': id_usuario,
            'tipo_usuario': tipo_usuario,
            'token': token
        }
    })

@app.route('/update_user', methods=['PUT'])
def update_user_simples():
    data = request.get_json()

    id_usuario = data.get('id_usuario')
    nome_completo = data.get('nome_completo')
    telefone = data.get('telefone')
    email = data.get('email')
    tipo_user = data.get('tipo_usuario')
    ativo = data.get('ativo')

    nome_completo = formatarNome(nome_completo)

    if nome_completo is None or email is None or tipo_user is None or ativo is None or id_usuario is None:
        return jsonify({
            'error': 'Dados incompletos.'
        }), 400

    cursor = con.cursor()
    cursor.execute("SELECT 1 FROM USUARIO WHERE TELEFONE = ? AND TELEFONE != '' AND ID_USUARIO != ?", (telefone, id_usuario))
    if cursor.fetchone():
        cursor.close()
        return jsonify({
            'error': 'Telefone já cadastrado.'
        }), 400

    cursor.execute(
        "SELECT 1 FROM USUARIO WHERE email = ? AND ID_USUARIO != ?",
        (email, id_usuario))
    if cursor.fetchone():
        cursor.close()
        return jsonify({
            'error': 'Email já cadastrado.'
        }), 400

    if not telefone:
        cursor.execute('''
               UPDATE USUARIO SET NOME_COMPLETO =?, EMAIL =?, TIPO_USUARIO =?, ATIVO =? WHERE ID_USUARIO =?
           ''', (nome_completo, email, tipo_user, ativo, id_usuario))
    else:
        cursor.execute('''
            UPDATE USUARIO SET NOME_COMPLETO =?, TELEFONE =?, EMAIL =?, TIPO_USUARIO =?, ATIVO =? WHERE ID_USUARIO =?
        ''', (nome_completo, telefone, email, tipo_user, ativo, id_usuario))

    con.commit()
    cursor.close()

    return jsonify({'success': "Informações atualizadas com sucesso!"}), 200

@app.route('/cadastro/<int:id>', methods=['PUT'])
def update_user(id):
    data = request.get_json()
    nome_completo = data.get('nome_completo')
    data_nascimento = data.get('data_nascimento')
    cpf_cnpj = data.get('cpf_cnpj')
    telefone = data.get('telefone')
    email = data.get('email')
    senha_hash = data.get('senha_hash')
    senha_nova = data.get('senha_nova')
    tipo_user = data.get('tipo_usuario')
    cursor = con.cursor()

    nome_completo = formatarNome(nome_completo)

    cursor.execute("SELECT ID_USUARIO FROM USUARIO WHERE CPF_CNPJ = ? AND ID_USUARIO != ?", (cpf_cnpj, id))
    if cursor.fetchone():
        cursor.close()
        return jsonify({
            'error': 'CPF/CNPJ já cadastrado.'
        }), 401

    cursor.execute("SELECT ID_USUARIO FROM USUARIO WHERE telefone = ? AND ID_USUARIO != ?", (telefone, id))
    if cursor.fetchone():
        cursor.close()
        return jsonify({
            'error': 'Telefone já cadastrado.'
        }), 401

    cursor.execute("SELECT 1 FROM USUARIO WHERE email = ? AND ID_USUARIO != ?", (email, id))
    if cursor.fetchone():
        cursor.close()
        return jsonify({
            'error': 'Email já cadastrado.'
        }), 400

    cursor.execute("SELECT ID_USUARIO, NOME_COMPLETO, DATA_NASCIMENTO, CPF_CNPJ, TELEFONE, EMAIL, SENHA_HASH, ATUALIZADO_EM FROM USUARIO WHERE id_usuario = ?", (id,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.close()
        return jsonify({'error': 'Usuário não encontrado.'}), 404

    if user_data[7] is not None:
        ultima_atualizacao = user_data[7]
        if datetime.now() - ultima_atualizacao < timedelta(hours=24):
            cursor.close()
            return jsonify({
                'error': 'Você só pode atualizar novamente após 24 horas da última atualização.'
            }), 403

    data_att = datetime.now()

    if not senha_nova and not senha_hash:
        if tipo_user == 1:
            cursor.execute("UPDATE USUARIO SET NOME_COMPLETO = ?, DATA_NASCIMENTO = ?, CPF_CNPJ = ?, TELEFONE = ?, EMAIL = ? WHERE id_usuario = ?",
                (nome_completo, data_nascimento, cpf_cnpj, telefone, email, id))
        else:
            cursor.execute(
                "UPDATE USUARIO SET NOME_COMPLETO = ?, DATA_NASCIMENTO = ?, CPF_CNPJ = ?, TELEFONE = ?, EMAIL = ?, ATUALIZADO_EM = ? WHERE id_usuario = ?",
                (nome_completo, data_nascimento, cpf_cnpj, telefone, email, data_att, id))

        con.commit()
        cursor.close()

        token = generate_token(id, email)

        return jsonify({
            'success': "Informações atualizadas com sucesso!",
            'user': {
                'id_usuario': id,
                'nome_completo': nome_completo,
                'data_nascimento': data_nascimento,
                'cpf_cnpj': cpf_cnpj,
                'telefone': telefone,
                'email': email,
                'token': token
            }
        })

    if not senha_nova and senha_hash:
        cursor.close()
        return jsonify({"error": "Informe uma nova senha para atualizá-la."}), 401

    if senha_nova and not senha_hash:
        cursor.close()
        return jsonify({"error": "Informe a senha atual para atualizá-la."}), 401

    if check_password_hash(user_data[6], senha_hash):
        if senha_hash == senha_nova:
            cursor.close()
            return jsonify({"error": "A senha nova não pode ser igual a senha antiga."}), 401
        senha_check = validar_senha(senha_nova)
        if senha_check is not True:
            cursor.close()
            return jsonify({"error": senha_check}), 404
        senha_enviada = generate_password_hash(senha_nova).decode('utf-8')
    else:
        cursor.close()
        return jsonify({"error": "Senha atual incorreta."}), 401

    if tipo_user == 1:
        cursor.execute(
            "UPDATE USUARIO SET NOME_COMPLETO = ?, DATA_NASCIMENTO = ?, CPF_CNPJ = ?, TELEFONE = ?, EMAIL = ?, SENHA_HASH = ? WHERE id_usuario = ?",
            (nome_completo, data_nascimento, cpf_cnpj, telefone, email, senha_enviada, id))
    else:
        cursor.execute(
            "UPDATE USUARIO SET NOME_COMPLETO = ?, DATA_NASCIMENTO = ?, CPF_CNPJ = ?, TELEFONE = ?, EMAIL = ?, SENHA_HASH = ?, ATUALIZADO_EM = ? WHERE id_usuario = ?",
            (nome_completo, data_nascimento, cpf_cnpj, telefone, email, senha_enviada, data_att, id))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Informações atualizadas com sucesso!",
        'user': {
            'nome_completo': nome_completo,
            'data_nascimento': data_nascimento,
            'cpf_cnpj': cpf_cnpj,
            'telefone': telefone,
            'email': email
        }
    })

@app.route('/cadastro/<int:id>', methods=['DELETE'])
def deletar_usuario(id):
    cursor = con.cursor()

    cursor.execute('SELECT 1 FROM USUARIO WHERE ID_USUARIO = ?', (id,))

    data = cursor.fetchone()

    if not data:
        return jsonify({
            'error': 'Usuário não encontrado.'
        })

    cursor.execute('''
        DELETE FROM USUARIO WHERE ID_USUARIO = ?
    ''', (id,))

    con.commit()

    # Apagar reservas ao deletar conta
    cursor.execute(
        'UPDATE CARROS SET RESERVADO = NULL, RESERVADO_EM = NULL, ID_USUARIO_RESERVA = NULL WHERE ID_USUARIO_RESERVA = ?',
        (id,)
    )

    # Apagar reservas ao deletar conta
    cursor.execute(
        'UPDATE MOTOS SET RESERVADO = NULL, RESERVADO_EM = NULL, ID_USUARIO_RESERVA = NULL WHERE ID_USUARIO_RESERVA = ?',
        (id,)
    )

    cursor.close()

    return jsonify({
        'success': 'Usuário deletado com sucesso!'
    })

tentativas = 0

@app.route('/login', methods=['POST'])
def login_user():
    global tentativas

    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha_hash')

    if not email or not senha:
        return jsonify({"error": "Todos os campos (email, senha) são obrigatórios."}), 400

    cursor = con.cursor()
    cursor.execute("SELECT id_usuario, email, nome_completo, data_nascimento, cpf_cnpj, telefone, senha_hash, ativo, tipo_usuario FROM USUARIO WHERE EMAIL = ?", (email,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.close()
        return jsonify({'error': 'Usuário não encontrado.'}), 401

    id_usuario = user_data[0]
    email = user_data[1]
    nome_completo = user_data[2]
    data_nascimento = user_data[3]
    cpf_cnpj = user_data[4]
    telefone = user_data[5]
    senha_hash = user_data[6]
    ativo = user_data[7]
    tipo_usuario = user_data[8]

    if not ativo:
        cursor.close()
        return jsonify({'error': 'Usuário inativo'}), 401

    if check_password_hash(senha_hash, senha):
        token = generate_token(id_usuario, email)
        tentativas = 0
        cursor.close()
        return jsonify({
            "success": "Login realizado com sucesso!",
            "dados": {
                'id_usuario': id_usuario,
                "email": email,
                "nome_completo": nome_completo,
                "data_nascimento": data_nascimento,
                "cpf_cnpj": cpf_cnpj,
                "telefone": telefone,
                "tipo_usuario": tipo_usuario,
                "token": token
            }
        })

    if tipo_usuario != 1:
        tentativas += 1

    if tentativas >= 3 and tipo_usuario != 1:
        cursor.execute("UPDATE USUARIO SET ATIVO = 0 WHERE id_usuario = ?", (id_usuario,))
        con.commit()
        cursor.close()
        return jsonify({"error": "Número máximo de tentativas de login excedido."}), 401

    return jsonify({"error": "Senha incorreta."}), 401 

# Verificar tipo usuário

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

@app.route('/obter_tipo_usuario', methods=['GET'])
def verificar_tipo_usuario():
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

    cursor.execute("SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?", (id_usuario,))

    tipo_usuario = cursor.fetchone()[0]

    cursor.close()

    return jsonify({
        'tipo_usuario': tipo_usuario
    })