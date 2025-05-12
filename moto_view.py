from flask import Flask, jsonify, request, send_from_directory, url_for, current_app, render_template
from main import app, con, upload_folder, senha_secreta, senha_app_email
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread
import smtplib
import pytz
import os
import jwt
import shutil

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

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

    if resultado[23]:
        cursor.execute('SELECT NOME_COMPLETO FROM USUARIO WHERE ID_USUARIO = ?', (resultado[23],))
        nome_usuario = cursor.fetchone()[0]
    else:
        nome_usuario = None

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
            'preco_venda': resultado[18],
            'placa': resultado[19],
            'alimentacao': resultado[20],
            'criado_em': resultado[21],
            'ativo': resultado[22],
            'nome_cliente': nome_usuario,
            'imagens': imagens
        }
    return None

def enviar_email_cancelamento(email_destinatario, tipo_veiculo, dados_veiculo):
    app_context = current_app._get_current_object()

    def task_envio():
        try:
            remetente = 'netcars.contato@gmail.com'
            senha = senha_app_email
            servidor_smtp = 'smtp.gmail.com'
            porta_smtp = 465

            # Data do cancelamento
            data_envio = datetime.now()
            data_cancelamento_str = data_envio.strftime("%d/%m/%Y")

            endereco_concessionaria = "Av. Exemplo, 1234 - Centro, Cidade Fictícia"

            assunto = "NetCars - Cancelamento de Reserva"

            # Renderiza o corpo do e-mail utilizando um template específico
            with app_context.app_context():
                corpo_email = render_template(
                    'email_cancelar_reserva.html',
                    email_destinatario=email_destinatario,
                    tipo_veiculo=tipo_veiculo,
                    dados_veiculo=dados_veiculo,
                    data_cancelamento_str=data_cancelamento_str,
                    endereco_concessionaria=endereco_concessionaria,
                    ano=datetime.now().year
                )

            # Configura o cabeçalho do e-mail
            msg = MIMEMultipart()
            msg['From'] = remetente
            msg['To'] = email_destinatario
            msg['Subject'] = assunto
            msg.attach(MIMEText(corpo_email, 'html'))

            try:
                # Usando conexão SSL para envio do e-mail
                server = smtplib.SMTP_SSL(servidor_smtp, porta_smtp, timeout=60)
                server.set_debuglevel(1)  # Ativa logs de debugging se necessário
                server.ehlo()  # Realiza a identificação junto ao servidor
                server.login(remetente, senha)
                text = msg.as_string()
                server.sendmail(remetente, email_destinatario, text)
                server.quit()
                print(f"E-mail de cancelamento enviado para {email_destinatario}")
            except Exception as e:
                print(f"Erro ao enviar e-mail de cancelamento: {e}")

        except Exception as e:
            print(f"Erro na tarefa de envio do e-mail: {e}")

    Thread(target=task_envio, daemon=True).start()

# Rota para servir as imagens de motos
@app.route('/uploads/motos/<int:id_moto>/<filename>')
def get_moto_image(id_moto, filename):
    return send_from_directory(os.path.join(app.root_path, upload_folder, 'Motos', str(id_moto)), filename)

# Buscar motos com filtros

@app.route('/cancelar-reserva-moto/<int:id>', methods=['DELETE'])
def cancelar_reserva_moto(id):
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

    # Buscar tipo de usuário
    cursor.execute('SELECT TIPO_USUARIO, EMAIL FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
    row_user = cursor.fetchone()
    tipo_user = row_user[0]
    email_user = row_user[1]

    try:
        if tipo_user in [1, 2]:
            cursor.execute('''
                UPDATE MOTOS SET RESERVADO = NULL, RESERVADO_EM = NULL, ID_USUARIO_RESERVA = NULL WHERE ID_MOTO =?
                ''', (id,))
        else:
            cursor.execute('''
                SELECT 1 FROM MOTOS WHERE RESERVADO IS TRUE AND ID_MOTO =? AND ID_USUARIO_RESERVA = ?
                ''', (id, id_usuario))
            check = cursor.fetchone()
            if check:
                cursor.execute('''
                   UPDATE MOTOS SET RESERVADO = NULL, RESERVADO_EM = NULL, ID_USUARIO_RESERVA = NULL WHERE ID_MOTO =?
                   ''', (id,))
            else:
                return jsonify({
                    'error': 'Apenas o dono da reserva pode cancelá-la.'
                }), 400
    except Exception as e:
        return jsonify({'error': e}), 400
    finally:
        # Buscar os dados da moto (para o e-mail)
        dados_moto = buscar_dados_moto_por_id(id)

        # Enviar o e-mail de cancelamento
        enviar_email_cancelamento(email_user, 'moto', dados_moto)

        con.commit()
        cursor.close()

        return jsonify({
            'success': 'Reserva cancelada com sucesso!'
        }), 200

# Buscar moto

@app.route('/buscar-moto', methods=['POST'])
def get_moto():
    data = request.get_json()

    idFiltro = data.get('id')

    query = '''
           SELECT id_moto, marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, renavam, 
                  marchas, partida, tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao, 
                  estado, cidade, quilometragem, preco_compra, preco_venda, placa, alimentacao, criado_em, ativo
           FROM MOTOS
       '''

    token = request.headers.get('Authorization')

    cursor = con.cursor()

    if token:
        token = remover_bearer(token)
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        id_usuario = payload['id_usuario']

        cursor.execute("SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?", (id_usuario,))
        tipo_user = cursor.fetchone()[0]

        if tipo_user == 3:
            cursor.execute('SELECT 1 FROM MOTOS WHERE RESERVADO IS TRUE AND ID_USUARIO_RESERVA = ? AND ID_MOTO = ?', (id_usuario, idFiltro))
        else:
            cursor.execute('SELECT 1 FROM MOTOS WHERE RESERVADO IS TRUE AND ID_MOTO = ?', (idFiltro,))

        usuario_reservou = cursor.fetchone()

        if tipo_user == 3:
            cursor.execute(
                '''
                SELECT 1
                FROM MOTOS
                INNER JOIN venda_compra
                ON MOTOS.id_moto = venda_compra.id_veiculo
                AND venda_compra.tipo_veiculo = 2
                WHERE venda_compra.id_usuario = ? AND MOTOS.ativo = 0
                AND motos.id_moto = ?
                ''', (id_usuario, idFiltro)
            )
        else:
            cursor.execute(
                '''
                SELECT 1
                FROM MOTOS
                INNER JOIN venda_compra
                ON MOTOS.id_moto = venda_compra.id_veiculo
                AND venda_compra.tipo_veiculo = 2
                WHERE MOTOS.ativo = 0 AND motos.id_moto = ?
                ''', (idFiltro,)
            )

        moto_vendida = cursor.fetchone()

        if usuario_reservou or moto_vendida:
                cursor.execute(f'{query} WHERE ID_MOTO = ?', (idFiltro,))

                moto = cursor.fetchone()

                images_dir = os.path.join(app.root_path, upload_folder, 'Motos', str(idFiltro))
                imagens = []
                if os.path.exists(images_dir):
                    for file in os.listdir(images_dir):
                        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                            imagem_url = url_for('get_moto_image', id_moto=idFiltro, filename=file, _external=True)
                            imagens.append(imagem_url)

                dados_moto = {
                    'id': moto[0],
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
                    'ativo': moto[22],
                    'imagens': imagens
                }

                cursor.close()

                if usuario_reservou:
                    return jsonify({
                        "reserva": True,
                        "veiculos": [dados_moto]
                    }), 200
                elif moto_vendida:
                    return jsonify({
                        "vendido": True,
                        "veiculos": [dados_moto]
                    }), 200

    anoMaxFiltro = data.get('ano-max')
    anoMinFiltro = data.get('ano-min')
    categoriaFiltro = data.get('categoria')
    cidadeFiltro = data.get('cidade')
    estadoFiltro = data.get('estado')
    marcaFiltro = data.get('marca')
    precoMax = data.get('preco-max')
    precoMinFiltro = data.get('preco-min')
    coresFiltro = data.get('cores')  # pode ser lista ou string
    nomeMoto = data.get('nome-veic')

    conditions = []
    params = []

    if idFiltro:
        conditions.append("id_moto = ?")
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
        if isinstance(coresFiltro, list):
            placeholders = ','.join('?' * len(coresFiltro))
            conditions.append(f"cor IN ({placeholders})")
            params.extend(coresFiltro)
        else:
            conditions.append("cor = ?")
            params.append(coresFiltro)
    if nomeMoto:
        nomeMoto = nomeMoto.lower()
        conditions.append('(LOWER(MARCA) LIKE ? OR LOWER(MODELO) LIKE ?)')
        params.append(f"%{nomeMoto}%")
        params.append(f"%{nomeMoto}%")

    conditions.append('ATIVO = 1')
    conditions.append('RESERVADO IS NOT TRUE')

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor = con.cursor()
    cursor.execute(query, params)
    fetch = cursor.fetchall()

    lista_motos = []
    for moto in fetch:

        id_moto = moto[0]
        images_dir = os.path.join(app.root_path, upload_folder, 'Motos', str(id_moto))
        imagens = []
        if os.path.exists(images_dir):
            for file in os.listdir(images_dir):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    imagem_url = url_for('get_moto_image', id_moto=id_moto, filename=file, _external=True)
                    imagens.append(imagem_url)

        lista_motos.append({
            'id': moto[0],
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
            'ativo': moto[22],
            'imagens': imagens
        })

    qnt_motos = len(lista_motos)

    return jsonify({
        'success': f'{qnt_motos} moto(s) encontrada(s).',
        'qnt': qnt_motos,
        'veiculos': lista_motos
    }), 200

# Upload de imagens para motos (requer autenticação e acesso de administrador)
@app.route('/moto/upload_img/<int:id>', methods=['POST'])
def upload_img_moto(id):
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

    # Verifica se o usuário possui acesso (administrador)
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

    pasta_destino = os.path.join(upload_folder, "Motos", str(id))
    os.makedirs(pasta_destino, exist_ok=True)

    saved_images = []
    for index, imagem in enumerate(imagens, start=1):
        nome_imagem = f"{index}.jpeg"
        imagem_path = os.path.join(pasta_destino, nome_imagem)
        imagem.save(imagem_path)
        saved_images.append(nome_imagem)

    return jsonify({
        'success': "Imagens adicionadas!"
    }), 200


@app.route('/moto/editar_img/<int:id>', methods=['PUT'])
def editar_imagens_moto(id):
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

    cursor.close()
    if user_type not in [1, 2]:
        return jsonify({'error': 'Acesso restrito a administradores'}), 403

    # Obtém as imagens e filtra somente as que possuem um nome (arquivo válido)
    imagens_brutas = request.files.getlist('imagens')
    imagens = [img for img in imagens_brutas if img and img.filename]
    if not imagens:
        return jsonify({
            'error': 'Dados incompletos',
            'missing_fields': 'Imagens'
        }), 400

    if len(imagens) < 3:
        return jsonify({
            'error': 'É necessário enviar ao menos 3 imagens',
        }), 400

    # Define a pasta destino para as imagens do veículo
    pasta_destino = os.path.join(upload_folder, "Motos", str(id))

    # Se a pasta já existir, apaga-a para remover as imagens antigas
    if os.path.exists(pasta_destino):
        try:
            shutil.rmtree(pasta_destino)
        except Exception as e:
            return jsonify({'error': f'Erro ao remover imagens antigas: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Veículo não encontrado'}), 400

    # Cria a pasta novamente para armazenar as novas imagens
    os.makedirs(pasta_destino, exist_ok=True)

    # Salva cada imagem na pasta, nomeando-as sequencialmente (1.jpeg, 2.jpeg, ...)
    for index, imagem in enumerate(imagens, start=1):
        nome_imagem = f"{index}.jpeg"
        imagem_path = os.path.join(pasta_destino, nome_imagem)
        try:
            imagem.save(imagem_path)
        except Exception as e:
            return jsonify({'error': f'Erro ao salvar a imagem: {str(e)}'}), 500

    return jsonify({'success': "Imagens atualizadas com sucesso!"}), 200

# Adicionar nova moto (requer autenticação e acesso de administrador)
@app.route('/moto', methods=['POST'])
def add_moto():
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

    # Verifica acesso de administrador
    cursor = con.cursor()
    cursor.execute('SELECT TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
    user_type = cursor.fetchone()[0]
    if user_type not in [1, 2]:
        return jsonify({'error': 'Acesso restrito a administradores'}), 403

    data = request.get_json()

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
            'error': f'Dados faltando: {missing_fields}'
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

    if int(quilometragem) < 0:
        return jsonify({
            'error': 'A quilometragem não pode ser negativa.'
        }), 400

    if float(preco_compra) < 0 or float(preco_venda) < 0:
        return jsonify({
            'error': 'O preço não pode ser negativo.'
        }), 400

    criado_em = datetime.now(pytz.timezone('America/Sao_Paulo'))

    # Verifica se já existe placa cadastrada
    cursor.execute("SELECT 1 FROM MOTOS WHERE PLACA = ?", (placa,))
    if cursor.fetchone():
        return jsonify({
            'error': 'Placa do veículo já cadastrada.'
        }), 409

    # Verifica se já existe RENAVAM cadastrado
    cursor.execute("SELECT 1 FROM MOTOS WHERE RENAVAM = ?", (renavam,))
    if cursor.fetchone():
        return jsonify({
            'error': 'Documento do veículo já cadastrada.'
        }), 409

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
            'licenciado': licenciado,
            'criado_em': criado_em,
            'ativo': ativo
        }
    }), 200

# Deletar moto (requer autenticação, verificação de administrador e remoção da pasta de imagens)
@app.route('/moto/<int:id>', methods=['DELETE'])
def deletar_moto(id):
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

    cursor.execute('SELECT 1 FROM MOTOS WHERE ID_MOTO = ?', (id,))
    if not cursor.fetchone():
        return jsonify({'error': 'Veículo não encontrado.'}), 404

    cursor.execute('DELETE FROM MOTOS WHERE ID_MOTO = ?', (id,))
    con.commit()
    cursor.close()

    pasta_destino = os.path.join(upload_folder, "Motos", str(id))
    full_path = os.path.join(app.root_path, pasta_destino)
    if os.path.exists(full_path):
        try:
            shutil.rmtree(full_path)
        except Exception as e:
            return jsonify({'error': f'Erro ao deletar a pasta do veículo: {str(e)}'}), 500

    return jsonify({
        'success': "Veículo deletado com sucesso!",
        'tipo_usuario': user_type
    }), 200

# Editar moto
@app.route('/moto/<int:id>', methods=['PUT'])
def editar_moto(id):
    cursor = con.cursor()

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
        SELECT marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, renavam, 
               marchas, partida, tipo_motor, cilindrada, freio_dianteiro_traseiro, 
               refrigeracao, estado, cidade, quilometragem, preco_compra, preco_venda, 
               placa, alimentacao, ativo, licenciado
        FROM MOTOS WHERE ID_MOTO = ?
    ''', (id,))

    data_ant = []
    for item in cursor.fetchone():
        data_ant.append(item)

    for i in range(len(data_ant)):
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
    licenciado = data.get('licenciado')

    ativo = data.get('ativo')

    cursor.execute('''
        UPDATE MOTOS
        SET marca = ?, modelo = ?, ano_modelo = ?, ano_fabricacao = ?, categoria = ?, cor = ?, 
            renavam = ?, marchas = ?, partida = ?, tipo_motor = ?, cilindrada = ?, 
            freio_dianteiro_traseiro = ?, refrigeracao = ?, estado = ?, cidade = ?, quilometragem = ?, 
            preco_compra = ?, preco_venda = ?, placa = ?, ativo = ?, alimentacao = ?, licenciado = ?
        WHERE ID_MOTO = ?
    ''', (marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, renavam, marchas, partida,
          tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao, estado, cidade,
          quilometragem, preco_compra, preco_venda, placa, ativo, alimentacao, licenciado, id))

    con.commit()
    cursor.close()

    return jsonify({
        'success': "Veículo editado com sucesso!",
        'dados': {
            'marca': marca,
            'modelo': modelo,
            'ano_modelo': ano_modelo,
            'ano_fabricacao': ano_fabricacao,
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
            'ativo': ativo,
            'licenciado': licenciado
        }
    }), 200
