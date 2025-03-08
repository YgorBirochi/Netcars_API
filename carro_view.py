from flask import Flask, jsonify, request
from main import app, con
from datetime import datetime
import pytz
import os, uuid

@app.route('/carro', methods=['GET'])
def get_carro():
    cursor = con.cursor()

    cursor.execute('''
    SELECT id_carro, marca, modelo, ano_modelo, ano_fabricacao, versao, cor, cambio, combustivel, categoria, 
    quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, criado_em, ativo FROM CARROS
    ''')

    fetch = cursor.fetchall()

    lista_carros = []

    for carro in list(fetch):
        lista_carros.append({
            'id_carro': carro[0],
            'marca': carro[1],
            'modelo': carro[2],
            'ano_modelo': carro[3],
            'ano_fabricacao': carro[4],
            'versao': carro[5],
            'cor': carro[6],
            'cambio': carro[7],
            'combustivel': carro[8],
            'categoria': carro[9],
            'quilometragem': carro[10],
            'estado': carro[11],
            'cidade': carro[12],
            'preco_compra': carro[13],
            'preco_venda': carro[14],
            'licenciado': carro[15],
            'placa': carro[16],
            'criado_em': carro[17],
            'ativo': carro[18]
        })

    qnt_carros = len(lista_carros)

    return jsonify({
        'success': f'{qnt_carros} carro(s) encontrado(s).',
        'veiculos': lista_carros
    }), 200



@app.route('/carro', methods=['POST'])
def add_carro():
    data = request.get_json()

    # Lista de campos obrigatórios
    required_fields = [
        'marca', 'modelo', 'ano_modelo', 'ano_fabricacao', 'versao',
        'cor', 'cambio', 'combustivel', 'categoria', 'quilometragem',
        'estado', 'cidade', 'preco_compra', 'preco_venda', 'placa'
    ]

    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return jsonify({
            'error': 'Dados incompletos.',
            'missing_fields': missing_fields
        }), 400


    marca = data.get('marca')
    modelo = data.get('modelo')
    ano_modelo = data.get('ano_modelo')
    ano_fabricacao = data.get('ano_fabricacao')
    versao = data.get('versao')
    cor = data.get('cor')
    cambio = data.get('cambio')
    combustivel = data.get('combustivel')
    categoria = data.get('categoria')
    quilometragem = data.get('quilometragem')
    estado = data.get('estado')
    cidade = data.get('cidade')
    preco_compra = data.get('preco_compra')
    preco_venda = data.get('preco_venda')
    licenciado = data.get('licenciado')
    placa = data.get('placa')
    ativo = 1

    # Alterando fuso horário para o de Brasília
    criado_em = datetime.now(pytz.timezone('America/Sao_Paulo'))

    cursor = con.cursor()

    cursor.execute('''
    INSERT INTO CARROS
    (marca, modelo, ano_modelo, ano_fabricacao, versao, cor, cambio, combustivel, categoria, 
    quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, criado_em, ativo)
    VALUES
    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (marca, modelo, ano_modelo, ano_fabricacao, versao, cor, cambio, combustivel, categoria,
    quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, placa, criado_em, ativo))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Veículo cadastrado com sucesso!",
        'dados': {
            'marca': marca,
            'modelo': modelo,
            'ano_modelo': ano_modelo,
            'ano_fabricacao': ano_fabricacao,
            'versao': versao,
            'cor': cor,
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
    cursor = con.cursor()

    cursor.execute('SELECT 1 FROM CARROS WHERE ID_CARRO = ?', (id,))

    if not cursor.fetchone():
        return jsonify({'error': 'Veículo não encontrado.'}), 404

    cursor.execute('DELETE FROM CARROS WHERE ID_CARRO = ?', (id,))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Veículo deletado com sucesso!"
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
        'cor', 'cambio', 'combustivel', 'categoria', 'quilometragem',
        'estado', 'cidade', 'preco_compra', 'preco_venda', 'licenciado',
        'placa', 'ativo'
    ]

    cursor.execute('''
        SELECT marca, modelo, ano_modelo, ano_fabricacao, versao, cor, cambio, combustivel, categoria, 
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
    cambio = data.get('cambio')
    combustivel = data.get('combustivel')
    categoria = data.get('categoria')
    quilometragem = data.get('quilometragem')
    estado = data.get('estado')
    cidade = data.get('cidade')
    preco_compra = data.get('preco_compra')
    preco_venda = data.get('preco_venda')
    licenciado = data.get('licenciado')
    placa = data.get('placa')
    ativo = data.get('ativo')

    cursor.execute('''
        UPDATE CARROS
        SET marca =?, modelo =?, ano_modelo =?, ano_fabricacao =?, versao =?, cor =?, cambio =?, combustivel =?, categoria =?, 
        quilometragem =?, estado =?, cidade =?, preco_compra =?, preco_venda =?, licenciado =?, placa =?, ativo =?
        where ID_CARRO = ?
        ''', (marca, modelo, ano_modelo, ano_fabricacao, versao, cor, cambio, combustivel, categoria,
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

# Rota para salvar as imagens em uma pasta com ID único
@app.route('/upload', methods=['POST'])
def upload():
    base_dir = 'assets/img'  # Certifique-se de que essa pasta exista ou crie-a

    # Gerar um ID único para a nova pasta (por exemplo, usando uuid)
    folder_id = str(uuid.uuid4())
    new_folder = os.path.join(base_dir, folder_id)
    os.makedirs(new_folder, exist_ok=True)

    # Obter os arquivos enviados
    files = request.files.getlist('files')
    if len(files) < 3:
        return jsonify({'error': 'Selecione pelo menos 3 arquivos.'}), 400

    for f in files:
        # Salva cada arquivo na nova pasta
        file_path = os.path.join(new_folder, f.filename)
        f.save(file_path)

    # Retorna a rota ou o id da pasta
    return jsonify({'folder': new_folder, 'folder_id': folder_id}), 200


