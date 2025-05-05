from flask import Flask, request, jsonify
from main import app, con, senha_secreta
import jwt

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

@app.route('/compra/a_vista', methods=['POST'])
def compra_a_vista():
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

    data = request.get_json()

    id_veic = data.get('id_veic')
    tipo_veic = data.get('tipo_veic')

    if not id_veic or not tipo_veic:
        return jsonify({'error': 'Dados incompletos'}), 400

    try:
        cursor = con.cursor()

        if tipo_veic == 1:
            cursor.execute('SELECT PRECO_VENDA FROM CARROS WHERE ID_CARRO = ?', (id_veic,))
        else:
            cursor.execute('SELECT PRECO_VENDA FROM MOTOS WHERE ID_MOTO = ?', (id_veic,))

        resposta = cursor.fetchone()

        if not resposta:
            return jsonify({'error': 'Veículo não encontrado'}), 400

        preco_venda = resposta[0]

        cursor.execute('''
                INSERT INTO VENDA_COMPRA 
                (TIPO_VENDA_COMPRA, VALOR_TOTAL, FORMA_PAGAMENTO, DATA_VENDA_COMPPRA, ID_USUARIO, TIPO_VEICULO, ID_VEICULO)
                VALUES (1, ?, 1, CURRENT_TIMESTAMP, ?, ?, ?)
            ''', (preco_venda, id_usuario, tipo_veic, id_veic))

        con.commit()

        return jsonify({'success': 'Sua compra foi efetuada com sucesso!'}), 200
    except Exception as e:
        print("error :" +e)
        return jsonify({"error": e}), 400
    finally:
        cursor.close()