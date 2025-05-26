from flask import Flask, request, jsonify, url_for
from main import app, con, senha_secreta, upload_folder
import jwt
import os

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

def buscar_dados_carro_por_id(id_carro):
    cursor = con.cursor()
    query = '''
        SELECT id_carro, marca, modelo, ano_modelo, ano_fabricacao, versao, cor, renavam,
               cambio, combustivel, categoria, quilometragem, estado, cidade, preco_compra,
               licenciado, placa, criado_em, ativo, id_usuario_reserva
        FROM CARROS
        WHERE id_carro = ?
    '''
    cursor.execute(query, (id_carro,))
    resultado = cursor.fetchone()

    if resultado[19]:
        cursor.execute('SELECT NOME_COMPLETO FROM USUARIO WHERE ID_USUARIO = ?', (resultado[19],))
        nome_usuario = cursor.fetchone()[0]
    else:
        nome_usuario = None

    cursor.execute('''
        SELECT VALOR_TOTAL 
        FROM VENDA_COMPRA 
        WHERE TIPO_VEICULO = 1 AND ID_VEICULO = ?
        AND TIPO_VENDA_COMPRA = 1
    ''', (id_carro,))

    preco_venda = cursor.fetchone()[0]

    cursor.close()

    # Define o caminho para a pasta de imagens do carro (ex: uploads/Carros/<id_carro>)
    images_dir = os.path.join(app.root_path, upload_folder, 'Carros', str(id_carro))
    imagens = []

    # Verifica se o diretório existe
    if os.path.exists(images_dir):
        for file in os.listdir(images_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                imagem_url = url_for('get_car_image', id_carro=id_carro, filename=file, _external=True)
                imagens.append(imagem_url)

    if resultado and imagens:
        return {
            'id': resultado[0],
            'marca': resultado[1],
            'modelo': resultado[2],
            'ano_modelo': resultado[3],
            'ano_fabricacao': resultado[4],
            'versao': resultado[5],
            'cor': resultado[6],
            'renavam': resultado[7],
            'cambio': resultado[8],
            'combustivel': resultado[9],
            'categoria': resultado[10],
            'quilometragem': resultado[11],
            'estado': resultado[12],
            'cidade': resultado[13],
            'preco_compra': resultado[14],
            'preco_venda': preco_venda,
            'licenciado': resultado[15],
            'placa': resultado[16],
            'criado_em': resultado[17],
            'ativo': resultado[18],
            'nome_cliente': nome_usuario,
            'imagens': imagens
        }
    return None

def buscar_dados_moto_por_id(id_moto):
    cursor = con.cursor()
    query = '''
        SELECT id_moto, marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, renavam, 
               marchas, partida, tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao,
               estado, cidade, quilometragem, preco_compra, preco_venda, placa, alimentacao, criado_em, ativo, id_usuario_reserva
        FROM MOTOS
        WHERE id_moto = ?
    '''
    cursor.execute(query, (id_moto,))
    resultado = cursor.fetchone()

    if resultado[22]:
        cursor.execute('SELECT NOME_COMPLETO FROM USUARIO WHERE ID_USUARIO = ?', (resultado[22],))
        nome_usuario = cursor.fetchone()[0]
    else:
        nome_usuario = None

    cursor.execute('''
            SELECT VALOR_TOTAL 
            FROM VENDA_COMPRA 
            WHERE TIPO_VEICULO = 2 AND ID_VEICULO = ?
            AND TIPO_VENDA_COMPRA = 1
        ''', (id_moto,))

    preco_venda = cursor.fetchone()[0]

    cursor.close()

    images_dir = os.path.join(app.root_path, upload_folder, 'Motos', str(id_moto))
    imagens = []
    if os.path.exists(images_dir):
        for file in os.listdir(images_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                imagem_url = url_for('get_moto_image', id_moto=id_moto, filename=file, _external=True)
                imagens.append(imagem_url)

    if resultado and imagens:
        return {
            'id': resultado[0],
            'marca': resultado[1],
            'modelo': resultado[2],
            'ano_modelo': resultado[3],
            'ano_fabricacao': resultado[4],
            'categoria': resultado[5],
            'cor': resultado[6],
            'renavam': resultado[7],
            'marchas': resultado[8],
            'partida': resultado[9],
            'tipo_motor': resultado[10],
            'cilindrada': resultado[11],
            'freio_dianteiro_traseiro': resultado[12],
            'refrigeracao': resultado[13],
            'estado': resultado[14],
            'cidade': resultado[15],
            'quilometragem': resultado[16],
            'preco_compra': resultado[17],
            'preco_venda': preco_venda,
            'placa': resultado[18],
            'alimentacao': resultado[19],
            'criado_em': resultado[20],
            'ativo': resultado[21],
            'nome_cliente': nome_usuario,
            'imagens': imagens
        }
    return None

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

        cursor.execute('SELECT 1 FROM VENDA_COMPRA WHERE ID_USUARIO = ? AND STATUS = 1', (id_usuario,))

        if cursor.fetchone():
            return jsonify({'error': 'Você já possui um financiamento em andamento.'}), 400

        if tipo_veic == 1:
            cursor.execute('SELECT PRECO_VENDA FROM CARROS WHERE ID_CARRO = ?', (id_veic,))
        else:
            cursor.execute('SELECT PRECO_VENDA FROM MOTOS WHERE ID_MOTO = ?', (id_veic,))

        resposta = cursor.fetchone()

        if not resposta:
            return jsonify({'error': 'Veículo não encontrado'}), 400

        preco_venda = resposta[0]

        if tipo_veic == 1:
            cursor.execute('''
                UPDATE CARROS 
                SET ATIVO = 0,
                RESERVADO = NULL,
                RESERVADO_EM = NULL,
                ID_USUARIO_RESERVA = NULL
                WHERE ID_CARRO = ?
            ''', (id_veic,))
        else:
            cursor.execute('''
                UPDATE MOTOS 
                SET ATIVO = 0,
                RESERVADO = NULL,
                RESERVADO_EM = NULL,
                ID_USUARIO_RESERVA = NULL
                WHERE ID_MOTO = ?
            ''', (id_veic,))

        cursor.execute('''
                INSERT INTO VENDA_COMPRA 
                (TIPO_VENDA_COMPRA, VALOR_TOTAL, FORMA_PAGAMENTO, DATA_VENDA_COMPRA, ID_USUARIO, TIPO_VEICULO, ID_VEICULO, STATUS)
                VALUES (1, ?, 1, CURRENT_TIMESTAMP, ?, ?, ?, 2)
            ''', (preco_venda, id_usuario, tipo_veic, id_veic))

        con.commit()

        return jsonify({'success': 'Compra efetuada com sucesso! Veja mais detalhes clicando em "Ver detalhes".'}), 200
    except Exception as e:
        print({"error": e})
        return jsonify({"error": e}), 400
    finally:
        cursor.close()


@app.route('/buscar_venda', methods=['GET'])
def buscar_venda():
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

    user = cursor.fetchone()

    if not user:
        return jsonify({
            'error': 'Usuário não encontrado.'
        }), 400

    tipo_usuario = user[0]

    if tipo_usuario in [1, 2]:
        cursor.execute(
            '''
            SELECT ID_CARRO
            FROM carros
            INNER JOIN venda_compra
            ON carros.id_carro = venda_compra.id_veiculo
            WHERE venda_compra.tipo_veiculo = 1 AND carros.ativo = 0
            AND venda_compra.status = 2
            '''
        )
        data_carro = cursor.fetchall()

        cursor.execute(
            '''
            SELECT ID_MOTO
            FROM motos
            INNER JOIN venda_compra
            ON motos.id_moto = venda_compra.id_veiculo
            WHERE venda_compra.tipo_veiculo = 2 AND motos.ativo = 0
            AND venda_compra.status = 2
            '''
        )
        data_moto = cursor.fetchall()
    else:
        cursor.execute(
            '''
            SELECT ID_CARRO
            FROM carros
            INNER JOIN venda_compra
            ON carros.id_carro = venda_compra.id_veiculo
            WHERE venda_compra.id_usuario = ? AND carros.ativo = 0
            AND venda_compra.tipo_veiculo = 1 AND venda_compra.status = 2
            ''', (id_usuario,)
        )
        data_carro = cursor.fetchall()

        cursor.execute(
            '''
            SELECT ID_MOTO
            FROM motos
            INNER JOIN venda_compra
            ON motos.id_moto = venda_compra.id_veiculo
            WHERE venda_compra.id_usuario = ? AND motos.ativo = 0
            AND venda_compra.tipo_veiculo = 2 AND venda_compra.status = 2
            ''', (id_usuario,)
        )
        data_moto = cursor.fetchall()

    id_carro = [row[0] for row in data_carro]
    dadosCarro = [buscar_dados_carro_por_id(id) for id in id_carro]

    id_moto = [row[0] for row in data_moto]
    dadosMoto = [buscar_dados_moto_por_id(id) for id in id_moto]

    return jsonify({
        'carros': dadosCarro,
        'motos': dadosMoto
    })
