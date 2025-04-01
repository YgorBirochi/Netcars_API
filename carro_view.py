from flask import Flask, jsonify, request, send_from_directory, url_for
from main import app, con, upload_folder, senha_secreta
from datetime import datetime
import pytz
import os, uuid
import jwt
import shutil

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

@app.route('/uploads/carros/<int:id_carro>/<filename>')
def get_car_image(id_carro, filename):
    return send_from_directory(os.path.join(app.root_path, 'upload', 'Carros', str(id_carro)), filename)

@app.route('/buscar-carro', methods=['POST'])
def get_carro():
    data = request.get_json()

    idFiltro = data.get('id')
    anoMaxFiltro = data.get('ano-max')
    anoMinFiltro = data.get('ano-min')
    categoriaFiltro = data.get('categoria')
    cidadeFiltro = data.get('cidade')
    estadoFiltro = data.get('estado')
    marcaFiltro = data.get('marca')
    precoMax = data.get('preco-max')
    precoMinFiltro = data.get('preco-min')
    coresFiltro = data.get('cores')  # Pode ser uma lista ou string

    # Query base
    query = '''
        SELECT id_carro, marca, modelo, ano_modelo, ano_fabricacao, versao, cor, renavam, cambio, combustivel, categoria, 
               quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, criado_em, ativo 
        FROM CARROS
    '''
    conditions = []
    params = []

    # Adiciona as condições de acordo com os filtros informados
    if idFiltro:
        conditions.append("id_carro = ?")
        params.append(idFiltro)
    if anoMaxFiltro:
        conditions.append("ano_modelo <= ?")
        params.append(anoMaxFiltro)
    if anoMinFiltro:
        conditions.append("ano_modelo >= ?")
        params.append(anoMinFiltro)
    if categoriaFiltro:
        conditions.append("categoria = ?")
        params.append(categoriaFiltro)
    if cidadeFiltro:
        conditions.append("cidade = ?")
        params.append(cidadeFiltro)
    if estadoFiltro:
        conditions.append("estado = ?")
        params.append(estadoFiltro)
    if marcaFiltro:
        conditions.append("marca = ?")
        params.append(marcaFiltro)
    if precoMax:
        conditions.append("preco_venda <= ?")
        params.append(precoMax)
    if precoMinFiltro:
        conditions.append("preco_venda >= ?")
        params.append(precoMinFiltro)
    if coresFiltro:
        # Se coresFiltro for uma lista, usamos IN; caso contrário, comparamos com igualdade
        if isinstance(coresFiltro, list):
            placeholders = ','.join('?' * len(coresFiltro))
            conditions.append(f"cor IN ({placeholders})")
            params.extend(coresFiltro)
        else:
            conditions.append("cor = ?")
            params.append(coresFiltro)

    # Se houver condições, concatena à query base
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor = con.cursor()
    cursor.execute(query, params)
    fetch = cursor.fetchall()

    lista_carros = []
    for carro in list(fetch):
        id_carro = carro[0]
        # Define o caminho para a pasta de imagens do carro (ex: uploads/Carros/<id_carro>)
        images_dir = os.path.join(app.root_path, upload_folder, 'Carros', str(id_carro))
        imagens = []

        # Verifica se o diretório existe
        if os.path.exists(images_dir):
            for file in os.listdir(images_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    imagem_url = url_for('get_car_image', id_carro=id_carro, filename=file, _external=True)
                    imagens.append(imagem_url)

        lista_carros.append({
            'id': carro[0],
            'marca': carro[1],
            'modelo': carro[2],
            'ano_modelo': carro[3],
            'ano_fabricacao': carro[4],
            'versao': carro[5],
            'cor': carro[6],
            'renavam': carro[7],
            'cambio': carro[8],
            'combustivel': carro[9],
            'categoria': carro[10],
            'quilometragem': carro[11],
            'estado': carro[12],
            'cidade': carro[13],
            'preco_compra': carro[14],
            'preco_venda': carro[15],
            'licenciado': carro[16],
            'placa': carro[17],
            'criado_em': carro[18],
            'ativo': carro[19],
            'imagens': imagens
        })

    qnt_carros = len(lista_carros)

    return jsonify({
        'success': f'{qnt_carros} carro(s) encontrado(s).',
        'qnt': qnt_carros,
        'veiculos': lista_carros
    }), 200

@app.route('/carro/upload_img/<int:id>', methods=['POST'])
def upload_img(id):
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

    imagens = request.files.getlist('imagens')

    if not imagens:
        return jsonify({
            'error': 'Dados incompletos',
            'missing_fields': 'Imagens'
        }), 400

    # Define a pasta destino usando o id do carro
    pasta_destino = os.path.join(upload_folder, "Carros", str(id))
    os.makedirs(pasta_destino, exist_ok=True)

    # Salva cada imagem na pasta, nomeando sequencialmente (1.jpeg, 2.jpeg, 3.jpeg, ...)
    saved_images = []  # para armazenar os nomes dos arquivos salvos
    for index, imagem in enumerate(imagens, start=1):
        nome_imagem = f"{index}.jpeg"
        imagem_path = os.path.join(pasta_destino, nome_imagem)
        imagem.save(imagem_path)
        saved_images.append(nome_imagem)

    return jsonify({
        'success': "Imagens adicionadas!"
    }), 200

@app.route('/carro', methods=['POST'])
def add_carro():
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
    if user_type not in [1,2]:
        return jsonify({'error': 'Acesso restrito a administradores'}), 403

    data = request.get_json()

    # Lista de campos obrigatórios
    required_fields = [
        'marca', 'modelo', 'ano_modelo', 'ano_fabricacao', 'versao',
        'cor', 'renavam', 'cambio', 'combustivel', 'categoria', 'quilometragem',
        'estado', 'cidade', 'preco_compra', 'preco_venda', 'licenciado', 'placa'
    ]

    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return jsonify({
            'error': f'Dados faltando: {missing_fields}'
        }), 400

    marca = data.get('marca')
    modelo = data.get('modelo')
    ano_modelo = data.get('ano_modelo')
    ano_fabricacao = data.get('ano_fabricacao')
    versao = data.get('versao')
    cor = data.get('cor')
    renavam = data.get('renavam')
    cambio = data.get('cambio')
    combustivel = data.get('combustivel')
    categoria = data.get('categoria')
    quilometragem = data.get('quilometragem')
    estado = data.get('estado')
    cidade = data.get('cidade')
    preco_compra = data.get('preco_compra')
    preco_venda = data.get('preco_venda')
    licenciado = data.get('licenciado')
    placa = data.get('placa').upper()
    ativo = 1

    if int(quilometragem) < 0:
        return jsonify({
            'error': 'A quilometragem não pode ser negativa.'
        }), 400

    if float(preco_compra) < 0 or float(preco_venda) < 0:
        return jsonify({
            'error': 'O preço não pode ser negativo.'
        }), 400

    # Alterando fuso horário para o de Brasília
    criado_em = datetime.now(pytz.timezone('America/Sao_Paulo'))

    # Retornar caso já exista placa cadastrada
    cursor.execute("SELECT 1 FROM CARROS WHERE PLACA = ?", (placa,))
    if cursor.fetchone():
        return jsonify({
            'error': 'Placa do veículo já cadastrada.'
        }), 409

    # Retornar caso já exista RENAVAM cadastrado
    cursor.execute("SELECT 1 FROM CARROS WHERE RENAVAM = ?", (renavam,))
    if cursor.fetchone():
        return jsonify({
            'error': 'Documento do veículo já cadastrado.'
        }), 409

    if (ano_fabricacao < ano_modelo):
        return jsonify({
            'error': 'Ano de fabricação não pode ser anterior ao ano do modelo.'
        }), 400

    if (preco_venda < preco_compra):
        return jsonify({
            'error': 'Preço de venda não pode ser menor ao preço de compra.'
        }), 400

    cursor.execute('''
        INSERT INTO CARROS
        (marca, modelo, ano_modelo, ano_fabricacao, versao, cor, renavam, cambio, combustivel, categoria, 
        quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, criado_em, ativo)
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)  RETURNING ID_CARRO
        ''', (marca, modelo, ano_modelo, ano_fabricacao, versao, cor, renavam, cambio, combustivel, categoria,
              quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, criado_em, ativo))

    id_carro = cursor.fetchone()[0]
    con.commit()

    cursor.close()

    return jsonify({
        'success': "Veículo cadastrado com sucesso!",
        'dados': {
            'id_carro': id_carro,
            'marca': marca,
            'modelo': modelo,
            'ano_modelo': ano_modelo,
            'ano_fabricacao': ano_fabricacao,
            'versao': versao,
            'cor': cor,
            'renavam': renavam,
            'cambio': cambio,
            'combustivel': combustivel,
            'categoria': categoria,
            'quilometragem': quilometragem,
            'estado': estado,
            'cidade': cidade,
            'preco_compra': preco_compra,
            'preco_venda': preco_venda,
            'licenciado': licenciado,
            'placa': placa,
            'criado_em': criado_em,
            'ativo': ativo
        }
    }), 200

@app.route('/carro/<int:id>', methods=['DELETE'])
def deletar_carro(id):
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
    if user_type not in [1,2]:
        return jsonify({'error': 'Acesso restrito a administradores'}), 403

    cursor = con.cursor()

    cursor.execute('SELECT 1 FROM CARROS WHERE ID_CARRO = ?', (id,))

    if not cursor.fetchone():
        return jsonify({'error': 'Veículo não encontrado.'}), 404

    cursor.execute('DELETE FROM CARROS WHERE ID_CARRO = ?', (id,))

    con.commit()
    cursor.close()

    pasta_destino = os.path.join(upload_folder, "Carros", str(id))

    # Verifica se a pasta existe e a remove
    if os.path.exists(pasta_destino):
        try:
            shutil.rmtree(pasta_destino)
        except Exception as e:
            return jsonify({'error': f'Erro ao deletar a pasta do veículo: {str(e)}'}), 500

    return jsonify({
        'success': "Veículo deletado com sucesso!",
        'tipo_usuario': user_type
    }), 200

@app.route('/carro/<int:id>', methods=['PUT'])
def editar_carro(id):
    cursor = con.cursor()

    # Verificando a existência do carro
    cursor.execute('SELECT 1 FROM CARROS WHERE ID_CARRO = ?', (id,))
    if not cursor.fetchone():
        return jsonify({'error': 'Veículo não encontrado.'}), 404

    data = request.get_json()
    fields = [
        'marca', 'modelo', 'ano_modelo', 'ano_fabricacao', 'versao',
        'cor', 'renavam', 'cambio', 'combustivel', 'categoria', 'quilometragem',
        'estado', 'cidade', 'preco_compra', 'preco_venda', 'licenciado',
        'placa', 'ativo'
    ]

    cursor.execute('''
        SELECT marca, modelo, ano_modelo, ano_fabricacao, versao, cor, renavam, cambio, combustivel, categoria, 
        quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, ativo
        FROM CARROS WHERE ID_CARRO = ?
    ''', (id,))

    data_ant = []
    for item in cursor.fetchone():
        data_ant.append(item)

    for i in range(len(data_ant)):
        print(fields[i])
        if data.get(fields[i]) == data_ant[i] or not data.get(fields[i]):
            data[fields[i]] = data_ant[i]

    marca = data.get('marca')
    modelo = data.get('modelo')
    ano_modelo = data.get('ano_modelo')
    ano_fabricacao = data.get('ano_fabricacao')
    versao = data.get('versao')
    cor = data.get('cor')
    renavam = data.get('renavam')
    cambio = data.get('cambio')
    combustivel = data.get('combustivel')
    categoria = data.get('categoria')
    quilometragem = data.get('quilometragem')
    estado = data.get('estado')
    cidade = data.get('cidade')
    preco_compra = data.get('preco_compra')
    preco_venda = data.get('preco_venda')
    licenciado = data.get('licenciado')
    placa = data.get('placa').upper()

    ativo = data.get('ativo')

    cursor.execute('''
        UPDATE CARROS
        SET marca =?, modelo =?, ano_modelo =?, ano_fabricacao =?, versao =?, cor =?, renavam =?, cambio =?, combustivel =?, categoria =?, 
        quilometragem =?, estado =?, cidade =?, preco_compra =?, preco_venda =?, licenciado =?, placa =?, ativo =?
        where ID_CARRO = ?
        ''', (marca, modelo, ano_modelo, ano_fabricacao, versao, cor, renavam, cambio, combustivel, categoria,
              quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, ativo, id))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Veículo editado com sucesso!",
        'dados': {
            'marca': marca,
            'modelo': modelo,
            'ano_modelo': ano_modelo,
            'ano_fabricacao': ano_fabricacao,
            'versao': versao,
            'cor': cor,
            'renavam': renavam,
            'cambio': cambio,
            'combustivel': combustivel,
            'categoria': categoria,
            'quilometragem': quilometragem,
            'estado': estado,
            'cidade': cidade,
            'preco_compra': preco_compra,
            'preco_venda': preco_venda,
            'licenciado': licenciado,
            'placa': placa,
            'ativo': ativo
        }
    }), 200


@app.route('/qnt_veiculos')
def qnt_veiculos():
    cursor = con.cursor()

    cursor.execute('''
        SELECT COUNT(*) AS qnt_carros
        FROM CARROS
        WHERE RESERVADO IS NULL
    ''')

    qnt_carros = cursor.fetchone()[0]

    cursor.execute('''
        SELECT COUNT(*) AS qnt_motos
        FROM MOTOS
        WHERE RESERVADO IS NULL
    ''')

    qnt_motos = cursor.fetchone()[0]

    cursor.close()

    return jsonify({
        'qnt_carros': qnt_carros,
        'qnt_motos': qnt_motos
    }), 200