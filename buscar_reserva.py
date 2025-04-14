import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask, request, jsonify, url_for, render_template, current_app
import jwt
from main import app, con, senha_app_email, senha_secreta, upload_folder
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
               preco_venda, licenciado, placa, criado_em, ativo, id_usuario_reserva
        FROM CARROS
        WHERE id_carro = ?
    '''
    cursor.execute(query, (id_carro,))
    resultado = cursor.fetchone()

    if resultado[20]:
        cursor.execute('SELECT NOME_COMPLETO FROM USUARIO WHERE ID_USUARIO = ?', (resultado[20],))
        nome_usuario = cursor.fetchone()[0]
    else:
        nome_usuario = None

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
            'preco_venda': resultado[15],
            'licenciado': resultado[16],
            'placa': resultado[17],
            'criado_em': resultado[18],
            'ativo': resultado[19],
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

@app.route('/buscar_reservas', methods=['GET'])
def buscar_reserva():
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
        cursor.execute("SELECT ID_CARRO FROM CARROS WHERE RESERVADO IS True")
        data_carro = cursor.fetchall()

        cursor.execute("SELECT ID_MOTO FROM MOTOS WHERE RESERVADO IS True")
        data_moto = cursor.fetchall()
    else:
        cursor.execute("SELECT ID_CARRO FROM CARROS WHERE RESERVADO IS True AND ID_USUARIO_RESERVA = ?", (id_usuario,))
        data_carro = cursor.fetchall()

        cursor.execute("SELECT ID_MOTO FROM MOTOS WHERE RESERVADO IS True AND ID_USUARIO_RESERVA = ?", (id_usuario,))
        data_moto = cursor.fetchall()

    id_carro = [row[0] for row in data_carro]
    dadosCarro = [buscar_dados_carro_por_id(id) for id in id_carro]

    id_moto = [row[0] for row in data_moto]
    dadosMoto = [buscar_dados_moto_por_id(id) for id in id_moto]

    return jsonify({
        'carros': dadosCarro,
        'motos': dadosMoto
    })

def enviar_email_reserva(email_destinatario, tipo_veiculo, dados_veiculo):
    app_context = current_app._get_current_object()

    def task_envio():
        try:
            remetente = 'netcars.contato@gmail.com'
            senha = senha_app_email
            servidor_smtp = 'smtp.gmail.com'
            porta_smtp = 465

            # Calcular data limite para comparecimento (3 dias a partir de hoje)
            data_envio = datetime.now()
            data_limite = data_envio + timedelta(days=3)
            data_limite_str = data_limite.strftime("%d/%m/%Y")

            endereco_concessionaria = "Av. Exemplo, 1234 - Centro, Cidade Fictícia"

            # Montar o corpo do e-mail
            assunto = "NetCars - Confirmação de Reserva"

            with app_context.app_context():
                corpo_email = render_template(
                    'email_reserva.html',
                    email_destinatario=email_destinatario,
                    tipo_veiculo=tipo_veiculo,
                    dados_veiculo=dados_veiculo,
                    data_limite_str=data_limite_str,
                    endereco_concessionaria=endereco_concessionaria,
                    ano=datetime.now().year
                )

            # Configurando o cabeçalho do e-mail
            msg = MIMEMultipart()
            msg['From'] = remetente
            msg['To'] = email_destinatario
            msg['Subject'] = assunto
            msg.attach(MIMEText(corpo_email, 'html'))

            try:
                # Usando SSL direto (mais confiável com Gmail)
                server = smtplib.SMTP_SSL(servidor_smtp, porta_smtp, timeout=60)
                server.set_debuglevel(1)  # Ative para debugging
                server.ehlo()  # Identifica-se ao servidor
                server.login(remetente, senha)
                text = msg.as_string()
                server.sendmail(remetente, email_destinatario, text)
                server.quit()
                print(f"E-mail de confirmação de reserva enviado para {email_destinatario}")
            except Exception as e:
                print(f"Erro ao enviar e-mail de reserva: {e}")

        except Exception as e:
            print(f"Erro na tarefa de envio do e-mail: {e}")

    Thread(target=task_envio, daemon=True).start()

@app.route('/reservar_veiculo', methods=["POST"])
def reservar_veiculo():
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
    id_veiculo = data.get('id_veiculo')
    tipo_veiculo = data.get('tipo_veiculo')

    if not id_veiculo or not id_usuario or not tipo_veiculo:
        return jsonify({"error": "Informações incompletas."}), 400

    cursor = con.cursor()
    cursor.execute('SELECT EMAIL, TIPO_USUARIO FROM USUARIO WHERE ID_USUARIO = ?', (id_usuario,))
    dados_user = cursor.fetchone()
    if not dados_user:
        return jsonify({'error': 'Cliente não encontrado.'}), 400

    cursor.execute('SELECT 1 FROM CARROS WHERE ID_USUARIO_RESERVA = ?', (id_usuario,))
    reserva_carro = cursor.fetchone()

    cursor.execute('SELECT 1 FROM MOTOS WHERE ID_USUARIO_RESERVA = ?', (id_usuario,))
    reserva_moto = cursor.fetchone()

    if reserva_carro or reserva_moto:
        return jsonify({'error': 'Parece que você já possui um veículo reservado...'}), 400

    if dados_user[1] != 3:
        return jsonify({'error': 'Apenas clientes podem fazer reservas.'}), 400

    email = dados_user[0]
    if tipo_veiculo == "carro":
        dados_veiculo = buscar_dados_carro_por_id(id_veiculo)
    elif tipo_veiculo == "moto":
        dados_veiculo = buscar_dados_moto_por_id(id_veiculo)
    else:
        return jsonify({'error': 'Tipo de veículo inválido.'}), 400

    if not dados_veiculo:
        return jsonify({'error': 'Veículo não encontrado.'}), 400

    # Verifica se o veículo já está reservado
    cursor.execute(f'SELECT RESERVADO FROM {tipo_veiculo}s WHERE ID_{tipo_veiculo} = ?', (id_veiculo,))
    row = cursor.fetchone()
    if row and row[0] is True:
        return jsonify({'error': 'Veículo já reservado.'}), 400

    # Atualiza a reserva no banco
    data_envio = datetime.now()
    cursor.execute(
        f'UPDATE {tipo_veiculo}s SET RESERVADO = true, RESERVADO_EM = ?, ID_USUARIO_RESERVA = ? WHERE ID_{tipo_veiculo} = ?',
        (data_envio, id_usuario, id_veiculo)
    )
    con.commit()
    cursor.close()

    # Envia o e-mail de reserva de forma assíncrona
    enviar_email_reserva(email, tipo_veiculo, dados_veiculo)

    return jsonify({'success': f"Um email com mais informações foi enviado para {email}"}), 200

@app.route('/atualizar_reservas', methods=['GET'])
def verificar_reserva():
    data_agora = datetime.now()
    cursor = con.cursor()

    qnt = 0

    # Verifica reservas de carros
    cursor.execute('SELECT ID_CARRO, RESERVADO_EM FROM CARROS WHERE RESERVADO IS TRUE')
    carros = cursor.fetchall()
    if carros:
        for carro in carros:
            id_carro, reservado_em = carro
            # Atualiza se a reserva expirou (data_agora maior que data da reserva + 3 dias)
            if data_agora > reservado_em + timedelta(days=3):
                cursor.execute(
                    'UPDATE CARROS SET RESERVADO = NULL, RESERVADO_EM = NULL, ID_USUARIO_RESERVA = NULL WHERE ID_CARRO = ?',
                    (id_carro,)
                )
                qnt += 1

    # Verifica reservas de motos
    cursor.execute('SELECT ID_MOTO, RESERVADO_EM FROM MOTOS WHERE RESERVADO IS TRUE')
    motos = cursor.fetchall()
    if motos:
        for moto in motos:
            id_moto, reservado_em = moto
            if data_agora > reservado_em + timedelta(days=3):
                cursor.execute(
                    'UPDATE MOTOS SET RESERVADO = NULL, RESERVADO_EM = NULL, ID_USUARIO_RESERVA = NULL WHERE ID_MOTO = ?',
                    (id_moto,)
                )
                qnt += 1

    cursor.close()  # Fecha o cursor antes de chamar commit
    con.commit()
    return jsonify({'success': f'{qnt} veículo(s) verificado(s).'}), 200
