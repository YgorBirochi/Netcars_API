from flask import Flask, jsonify, request
from main import app, con, senha_secreta
import re
from flask_bcrypt import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

def generate_token(user_id):
    payload = {'id_usuario': user_id}
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

@app.route('/cadastro', methods=['GET'])
def get_user():
    cursor = con.cursor()

    cursor.execute('SELECT ID_USUARIO, NOME_COMPLETO, EMAIL, SENHA_HASH FROM USUARIO')

    resultado = cursor.fetchall()

    user_dic = []
    for user in resultado:
        user_dic.append({
            'id_usuario': user[0],
            'nome_completo': user[1],
            'email': user[2],
            'senha_hash': user[3]
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

    cursor = con.cursor()
    cursor.execute("SELECT 1 FROM USUARIO WHERE email = ?", (email,))

    if cursor.fetchone():
        return jsonify({'error': 'Email já cadastrado'}), 400

    senha_check = validar_senha(senha)
    if senha_check is not True:
        return jsonify({'error': senha_check}), 400

    senha_hash = generate_password_hash(senha).decode('utf-8')

    cursor.execute("INSERT INTO USUARIO (nome_completo, email, senha_hash, ativo, tipo_usuario) VALUES (?, ?, ?, 1, ?)", (nome, email, senha_hash, tipo_usuario))
    con.commit()

    cursor.execute('SELECT ID_USUARIO FROM USUARIO WHERE EMAIL = ?', (email,))
    id = cursor.fetchone()[0]
    cursor.close()

    return jsonify({
        'success': "Email cadastrado com sucesso!",
        'dados': {
            'nome_completo': nome,
            'email': email,
            'id_usuario': id,
            'tipo_usuario': tipo_usuario
        }
    })

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

    cursor = con.cursor()

    cursor.execute("SELECT ID_USUARIO FROM USUARIOS WHERE CPF_CNPJ = ?", (cpf_cnpj,))
    if cursor.fetchone():
        return jsonify({
            'error': 'CPF/CNPJ já cadastrado'
        })

    cursor.execute("SELECT ID_USUARIO FROM USUARIOS WHERE telefone = ?", (telefone,))
    if cursor.fetchone():
        return jsonify({
            'error': 'Telefone já cadastrado'
        })

    cursor.execute("SELECT ID_USUARIO, NOME_COMPLETO, DATA_NASCIMENTO, CPF_CNPJ, TELEFONE, EMAIL, SENHA_HASH, ATUALIZADO_EM FROM USUARIO WHERE id_usuario = ?", (id,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.close()
        return jsonify({'error': 'Usuário não encontrado'}), 404

    cursor.execute("SELECT 1 FROM USUARIO WHERE email = ?", (email,))

    if email != user_data[5]:
        if cursor.fetchone():
            return jsonify({'error': 'Email já cadastrado'}), 404

    if user_data[7] is not None:
        ultima_atualizacao = user_data[7]
        if datetime.now() - ultima_atualizacao < timedelta(hours=24):
            cursor.close()
            return jsonify({
                'error': 'Você só pode atualizar novamente após 24 horas da última atualização.'
            }), 403

    data_att = datetime.now()
    if not senha_nova and not senha_hash:
        cursor.execute("UPDATE USUARIO SET NOME_COMPLETO = ?, DATA_NASCIMENTO = ?, CPF_CNPJ = ?, TELEFONE = ?, EMAIL = ?, ATUALIZADO_EM = ? WHERE id_usuario = ?",
            (nome_completo, data_nascimento, cpf_cnpj, telefone, email, data_att, id))
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

    if not senha_nova and senha_hash:
        return jsonify({"error": "Digite uma nova senha para atualizá-la."}), 401

    if check_password_hash(user_data[6], senha_hash):
        senha_check = validar_senha(senha_nova)
        if senha_check is not True:
            return jsonify({'error': senha_check}), 404
        senha_enviada = generate_password_hash(senha_nova).decode('utf-8')
    else:
        return jsonify({"error": "Senha atual incorreta."}), 401

    cursor.execute("UPDATE USUARIO SET NOME_COMPLETO = ?, DATA_NASCIMENTO = ?, CPF_CNPJ = ?, TELEFONE = ?, EMAIL = ?, SENHA_HASH = ?, ATUALIZADO_EM = ? WHERE id_usuario = ?",
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

    cursor.execute('SELECT ID_USUARIO FROM USUARIO')

    possui_id = False
    for i in cursor.fetchall():
        if i[0] == id:
            possui_id = True

    if possui_id == False:
        return jsonify({
            'error': 'Usuário não encontrado.'
        })

    cursor.execute('''
        DELETE FROM USUARIO WHERE ID_USUARIO = ?
    ''', (id,))

    con.commit()
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
        token = generate_token(id_usuario)
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
