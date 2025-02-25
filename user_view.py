from flask import Flask, jsonify, request
from main import app, con
import re
from flask_bcrypt import generate_password_hash, check_password_hash

def validar_senha(senha):
    if len(senha) < 8:
        return jsonify({"error": "A senha deve ter pelo menos 8 caracteres."}), 400

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):
        return jsonify({"error": "A senha deve conter pelo menos um símbolo especial (!@#$%^&*...)."}), 400

    if not re.search(r"[A-Z]", senha):
        return jsonify({"error": "A senha deve conter pelo menos uma letra maiúscula."}), 400

    return True

@app.route('/user', methods=['GET'])
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

@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    nome = data.get('nome_completo')
    email = data.get('email')
    senha = data.get('senha_hash')
    tipo_usuario = data.get('tipo_usuario')

    cursor = con.cursor()
    cursor.execute("SELECT 1 FROM USUARIO WHERE email = ?", (email,))

    if cursor.fetchone():
        return jsonify({'message': 'Email já cadastrado'}), 400

    senha_check = validar_senha(senha)
    if senha_check is not True:
        return senha_check

    senha_hash = generate_password_hash(senha).decode('utf-8')

    cursor.execute("INSERT INTO USUARIO (nome_completo, email, senha_hash, ativo, tipo_usuario) VALUES (?, ?, ?, 1, ?)", (nome, email, senha_hash, tipo_usuario))

    con.commit()
    cursor.close()

    return jsonify({
        'message': "Email cadastrado com sucesso!",
        'user': {
            'nome': nome,
            'email': email
        }
    })

@app.route('/user/<int:id>', methods=['PUT'])
def update_user(id):
    cursor = con.cursor()

    cursor.execute("SELECT ID_USUARIO, NOME_COMPLETO, DATA_NASCIMENTO, CPF_CNPJ, TELEFONE, EMAIL, SENHA_HASH FROM USUARIO WHERE id_usuario = ?", (id,))
    user_data = cursor.fetchone()

    if not user_data:
        cursor.close()
        return jsonify({'message': 'Usuário não encontrado'}), 404

    data = request.get_json()
    nome = data.get('nome_completo', user_data[1])
    data_nascimento = data.get('data_nascimento', user_data[2])
    cpf_cnpj = data.get('cpf_cnpj', user_data[3])
    telefone = data.get('telefone', user_data[4])
    email = data.get('email', user_data[5])
    senha = data.get('senha_hash', user_data[6])

    cursor.execute("SELECT 1 FROM USUARIO WHERE email = ?", (email,))

    if email != user_data[5]:
        if cursor.fetchone():
            return jsonify({'message': 'Email já cadastrado'}), 400

    if senha != user_data[6]:
        senha_hash = generate_password_hash(senha).decode('utf-8')

    cursor.execute("UPDATE USUARIO SET NOME_COMPLETO = ?, DATA_NASCIMENTO = ?, CPF_CNPJ = ?, TELEFONE = ?, EMAIL = ?, SENHA_HASH = ? WHERE id_usuario = ?",
                   (nome, data_nascimento, cpf_cnpj, telefone, email, senha_hash, id))

    con.commit()
    cursor.close()

    return jsonify({
        'message': "Informações atualizadas com sucesso!",
        'user': {
            'nome_completo': nome,
            'data_nascimento': data_nascimento,
            'cpf_cnpj': cpf_cnpj,
            'telefone': telefone,
            'email': email,
        }
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
        return jsonify({'message': 'Usuário não encontrado.'}), 401

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
        return jsonify({'message': 'Usuário inativo'}), 401

    if check_password_hash(senha_hash, senha):
        tentativas = 0
        cursor.close()
        return jsonify({
            "message": "Login realizado com sucesso!",
            "dados_user": {
                'id_usuario': id_usuario,
                "email": email,
                "nome_completo": nome_completo,
                "data_nascimento": data_nascimento,
                "cpf_cnpj": cpf_cnpj,
                "telefone": telefone,
                "ativo": ativo
            }
        })

    if tipo_usuario != 1:
        tentativas += 1

    if tentativas >= 3 and tipo_usuario != 1:
        cursor.execute("UPDATE USUARIO SET ATIVO = 0 WHERE id_usuario = ?", (id_usuario,))
        con.commit()
        cursor.close()
        return jsonify({"error": "Número máximo de tentativas de login excedido."}), 401

    con.commit()
    cursor.close()
    return jsonify({"error": "Credenciais incorretas."}), 401
