from flask import Flask, jsonify, request
from main import app, con, upload_folder, senha_secreta
from datetime import datetime
import pytz
import os, uuid
import jwt

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

@app.route('/moto', methods=['GET'])
def get_moto():
    cursor = con.cursor()

    cursor.execute('''
    SELECT marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, renavam, marchas, partida, tipo_motor, 
        cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem, 
        preco_compra, preco_venda, placa, alimentacao, criado_em, ativo FROM MOTOS
    ''')

    fetch = cursor.fetchall()

    lista_motos = []

    for moto in fetch:
        lista_motos.append({
            'id_moto': moto[0],
            'marca': moto[1],
            'modelo': moto[2],
            'ano_modelo': moto[3],
            'ano_fabricacao': moto[4],
            'categoria': moto[5],
            'cor': moto[6],
            'renavam': moto[7],
            'marchas': moto[8],
            'partida': moto[9],
            'tipo_motor': moto[10],
            'cilindrada': moto[11],
            'freio_dianteiro_traseiro': moto[12],
            'refrigeracao': moto[13],
            'estado': moto[14],
            'cidade': moto[15],
            'quilometragem': moto[16],
            'preco_compra': moto[17],
            'preco_venda': moto[18],
            'placa': moto[19],
            'alimentacao': moto[20],
            'criado_em': moto[21],
            'ativo': moto[22]
        })

    qnt_motos = len(lista_motos)

    return jsonify({
        'success': f'{qnt_motos} moto(s) encontrada(s).',
        'veiculos': lista_motos
    }), 200


@app.route('/moto/upload_img/<int:id>', methods=['POST'])
def upload_img_moto(id):
    imagens = request.files.getlist('imagens')

    if not imagens:
        return jsonify({
            'error': 'Dados incompletos',
            'missing_fields': 'Imagens'
        }), 400

    # Define a pasta destino usando o id do carro
    pasta_destino = os.path.join(upload_folder, "Motos", str(id))
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

@app.route('/moto', methods=['POST'])
def add_moto():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token de autenticação necessário.'}), 401

    token = remover_bearer(token)
    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        id_usuario = payload['id_usuario']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado.'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido.'}), 401

    data = request.get_json()

    # Lista de campos obrigatórios
    required_fields = [
        'marca', 'modelo', 'ano_modelo', 'ano_fabricacao', 'categoria',
        'cor', 'renavam', 'marchas', 'partida', 'tipo_motor', 'cilindrada',
        'freio_dianteiro_traseiro', 'refrigeracao', 'estado', 'cidade',
        'quilometragem', 'preco_compra', 'preco_venda', 'placa',
        'alimentacao', 'licenciado'
    ]

    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return jsonify({
            'error': 'Dados incompletos',
            'missing_fields': missing_fields
        }), 400

    marca = data.get('marca')
    modelo = data.get('modelo')
    ano_modelo = data.get('ano_modelo')
    ano_fabricacao = data.get('ano_fabricacao')
    categoria = data.get('categoria')
    cor = data.get('cor')
    renavam = data.get('renavam')
    marchas = data.get('marchas')
    partida = data.get('partida')
    tipo_motor = data.get('tipo_motor')
    cilindrada = data.get('cilindrada')
    freio_dianteiro_traseiro = data.get('freio_dianteiro_traseiro')
    refrigeracao = data.get('refrigeracao')
    estado = data.get('estado')
    cidade = data.get('cidade')
    quilometragem = data.get('quilometragem')
    preco_compra = data.get('preco_compra')
    preco_venda = data.get('preco_venda')
    placa = data.get('placa').upper()
    alimentacao = data.get('alimentacao')
    licenciado = data.get('licenciado')
    ativo = 1

    # Alterando fuso horário para o de Brasília
    criado_em = datetime.now(pytz.timezone('America/Sao_Paulo'))

    cursor = con.cursor()

    cursor.execute('''
    INSERT INTO MOTOS
    (marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, renavam, marchas, partida, 
    tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem, 
    preco_compra, preco_venda, placa, criado_em, ativo, alimentacao, licenciado)
    VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING ID_MOTO
    ''', (marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, renavam, marchas, partida,
    tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem,
    preco_compra, preco_venda, placa, criado_em, ativo, alimentacao, licenciado))

    id_moto = cursor.fetchone()[0]
    con.commit()

    cursor.close()

    return jsonify({
        'success': "Veículo cadastrado com sucesso!",
        'dados': {
            'id_moto': id_moto,
            'marca': marca,
            'modelo': modelo,
            'ano_modelo': ano_modelo,
            'ano_fabricacao': ano_fabricacao,
            'categoria': categoria,
            'cor': cor,
            'renavam': renavam,
            'licenciado': licenciado,
            'marchas': marchas,
            'partida': partida,
            'tipo_motor': tipo_motor,
            'cilindrada': cilindrada,
            'freio_dianteiro_traseiro': freio_dianteiro_traseiro,
            'refrigeracao': refrigeracao,
            'estado': estado,
            'cidade': cidade,
            'quilometragem': quilometragem,
            'preco_compra': preco_compra,
            'preco_venda': preco_venda,
            'placa': placa,
            'alimentacao': alimentacao,
            'criado_em': criado_em,
            'ativo': ativo
        }
    }), 200

@app.route('/moto/<int:id>', methods=['DELETE'])
def deletar_moto(id):
    cursor = con.cursor()

    cursor.execute('SELECT 1 FROM motos WHERE ID_MOTO = ?', (id,))

    if not cursor.fetchone():
        return jsonify({'error': 'Veículo não encontrado.'}), 404

    cursor.execute('DELETE FROM MOTOS WHERE ID_MOTO = ?', (id,))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Veículo deletado com sucesso!"
    })

@app.route('/moto/<int:id>', methods=['PUT'])
def editar_moto(id):
    cursor = con.cursor()

    # Verificando a existência do carro
    cursor.execute('SELECT 1 FROM MOTOS WHERE ID_MOTO = ?', (id,))
    if not cursor.fetchone():
        return jsonify({'error': 'Veículo não encontrado.'}), 404

    data = request.get_json()

    fields = [
        'marca', 'modelo', 'ano_modelo', 'ano_fabricacao', 'categoria',
        'cor', 'renavam', 'marchas', 'partida', 'tipo_motor', 'cilindrada',
        'freio_dianteiro_traseiro', 'refrigeracao', 'estado', 'cidade',
        'quilometragem', 'preco_compra', 'preco_venda', 'placa', 'alimentacao',
        'ativo', 'licenciado'
    ]

    cursor.execute('''
        SELECT marca, modelo, ano_modelo, ano_fabricacao, licenciado, categoria, cor, renavam, marchas, 
        partida, tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade, 
        quilometragem, preco_compra, preco_venda, placa, criado_em, ativo, alimentacao
        FROM MOTOS WHERE ID_MOTO = ?
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
    categoria = data.get('categoria')
    cor = data.get('cor')
    renavam = data.get('renavam')
    marchas = data.get('marchas')
    partida = data.get('partida')
    tipo_motor = data.get('tipo_motor')
    cilindrada = data.get('cilindrada')
    freio_dianteiro_traseiro = data.get('freio_dianteiro_traseiro')
    refrigeracao = data.get('refrigeracao')
    estado = data.get('estado')
    cidade = data.get('cidade')
    quilometragem = data.get('quilometragem')
    preco_compra = data.get('preco_compra')
    preco_venda = data.get('preco_venda')
    placa = data.get('placa').upper()
    alimentacao = data.get('alimentacao')
    ativo = data.get('ativo')
    criado_em = data.get('criado_em')
    licenciado = data.get('licenciado')

    cursor.execute('''
        UPDATE MOTOS
        SET marca =?, modelo =?, ano_modelo =?, ano_fabricacao =?, categoria =?, cor =?, renavam = ?, marchas =?, partida =?, 
        tipo_motor =?, cilindrada=?, freio_dianteiro_traseiro =?, refrigeracao, =?, estado =?, cidade =?,  quilometragem =?, 
        preco_compra =?, preco_venda =?, placa =?, criado_em = ?, ativo =?, alimentacao =?, licenciado =?
        where ID_MOTO = ?
        ''',
       (marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, renavam, marchas, partida,
        tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade,
        quilometragem, preco_compra, preco_venda, placa, criado_em, ativo, alimentacao, licenciado))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Veículo editado com sucesso!",
        'dados': {
            'marca': marca,
            'modelo': modelo,
            'ano_modelo': ano_modelo,
            'ano_fabricacao': ano_fabricacao,
            'licenciado': licenciado,
            'categoria': categoria,
            'cor': cor,
            'renavam': renavam,
            'marchas': marchas,
            'partida': partida,
            'tipo_motor': tipo_motor,
            'cilindrada': cilindrada,
            'freio_dianteiro_traseiro': freio_dianteiro_traseiro,
            'refrigeracao': refrigeracao,
            'estado': estado,
            'cidade': cidade,
            'quilometragem': quilometragem,
            'preco_compra': preco_compra,
            'preco_venda': preco_venda,
            'placa': placa,
            'alimentacao': alimentacao,
            'criado_em': criado_em,
            'ativo': ativo
        }
    }), 200