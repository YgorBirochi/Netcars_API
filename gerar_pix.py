from flask import Flask, send_file, jsonify, request, current_app, render_template
from qrcode.constants import ERROR_CORRECT_H
from main import app, con, senha_app_email, senha_secreta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread
from io import BytesIO
from datetime import datetime, timedelta
from PIL import Image
import os
import crcmod
import qrcode
import smtplib
import jwt
import requests


def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token

def enviar_email_qrcode(email_destinatario, dados_user, nome_usuario, payload_completo):
    app_context = current_app._get_current_object()

    def task_envio():
        try:
            remetente = 'netcars.contato@gmail.com'
            senha = senha_app_email
            servidor_smtp = 'smtp.gmail.com'
            porta_smtp = 465

            # Calcular data limite para pagamento
            data_envio = datetime.now()
            data_limite = data_envio + timedelta(days=1)
            data_limite_str = data_limite.strftime("%d/%m/%Y")

            endereco_concessionaria = "Av. Exemplo, 1234 - Centro, Cidade Fictícia"

            # Montar o corpo do e-mail
            assunto = "NetCars - Confirmação de Pagamento"

            with app_context.app_context():
                corpo_email = render_template(
                    'email_pix.html',
                    nome_usuario=nome_usuario,
                    email_destinatario=email_destinatario,
                    dados_user=dados_user,
                    payload_completo=payload_completo,
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
                print(f"E-mail de pagamento do pix enviado para {email_destinatario}")
            except Exception as e:
                print(f"Erro ao enviar e-mail de pagamento: {e}")

        except Exception as e:
            print(f"Erro na tarefa de envio do e-mail: {e}")

    Thread(target=task_envio, daemon=True).start()

def calcula_crc16(payload):
    crc16 = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, rev=False)
    crc = crc16(payload.encode('utf-8'))
    return f"{crc:04X}"

def format_tlv(id, value):
    return f"{id}{len(value):02d}{value}"


@app.route('/gerar_pix', methods=['POST'])
def gerar_pix():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Token de autenticação necessário'}), 401

    token = remover_bearer(token)
    try:
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        email = payload['email']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token inválido'}), 401

    try:
        data = request.get_json()
        if not data or 'valor' not in data:
            return jsonify({"erro": "O valor do PIX é obrigatório."}), 400

        valor = f"{float(data['valor']):.2f}"

        cursor = con.cursor()
        cursor.execute("SELECT cg.RAZAO_SOCIAL, cg.CHAVE_PIX, cg.CIDADE FROM CONFIG_GARAGEM cg")
        resultado = cursor.fetchone()
        cursor.close()

        if not resultado:
            return jsonify({"erro": "Chave PIX não encontrada"}), 404

        nome, chave_pix, cidade = resultado
        nome = nome[:25] if nome else "Recebedor PIX"
        cidade = cidade[:15] if cidade else "Cidade"

        # Monta o campo 26 (Merchant Account Information) com TLVs internos
        merchant_account_info = (
                format_tlv("00", "br.gov.bcb.pix") +
                format_tlv("01", chave_pix)
        )
        campo_26 = format_tlv("26", merchant_account_info)

        payload_sem_crc = (
                "000201" +  # Payload Format Indicator
                "010212" +  # Point of Initiation Method
                campo_26 +  # Merchant Account Information
                "52040000" +  # Merchant Category Code
                "5303986" +  # Currency - 986 = BRL
                format_tlv("54", valor) +  # Transaction amount
                "5802BR" +  # Country Code
                format_tlv("59", nome) +  # Merchant Name
                format_tlv("60", cidade) +  # Merchant City
                format_tlv("62", format_tlv("05", "***")) +  # Additional data (TXID)
                "6304"  # CRC placeholder
        )

        crc = calcula_crc16(payload_sem_crc)
        payload_completo = payload_sem_crc + crc

        # Criação do QR Code com configurações aprimoradas
        qr_obj = qrcode.QRCode(
            version=None,  # Permite ajuste automático da versão
            error_correction=ERROR_CORRECT_H,  # Alta correção de erros (30%)
            box_size=10,
            border=4
        )
        qr_obj.add_data(payload_completo)
        qr_obj.make(fit=True)
        qr = qr_obj.make_image(fill_color="black", back_color="white")

        # Cria a pasta 'upload/qrcodes' relativa ao diretório do projeto
        pasta_qrcodes = os.path.join(os.getcwd(), "upload", "qrcodes")
        os.makedirs(pasta_qrcodes, exist_ok=True)

        # Conta quantos arquivos já existem com padrão 'pix_*.png'
        arquivos_existentes = [f for f in os.listdir(pasta_qrcodes) if f.startswith("pix_") and f.endswith(".png")]
        numeros_usados = []
        for nome_arq in arquivos_existentes:
            try:
                num = int(nome_arq.replace("pix_", "").replace(".png", ""))
                numeros_usados.append(num)
            except ValueError:
                continue
        proximo_numero = max(numeros_usados, default=0) + 1
        nome_arquivo = f"pix_{proximo_numero}.png"
        caminho_arquivo = os.path.join(pasta_qrcodes, nome_arquivo)

        # Salva o QR Code no disco
        qr.save(caminho_arquivo)

        # Substitua pelo seu Client-ID
        client_id = '2b7b62f0f313a32'

        headers = {
            'Authorization': f'Client-ID {client_id}',
        }

        url = 'https://api.imgur.com/3/image'

        # Abre a imagem e envia
        with open(caminho_arquivo, 'rb') as image_file:
            data = {
                'type': 'image',
                'title': 'Pix',
                'description': 'Pagamento de Teste'
            }
            files = {
                'image': image_file
            }
            response = requests.post(url, headers=headers, data=data, files=files)

        # Mostra a resposta
        print(response.status_code)
        print(response.json())

        # Verifica o status e exibe o link
        if response.status_code == 200:
            json_response = response.json()
            image_link = json_response['data']['link']
            print(f' Upload feito com sucesso! Link da imagem: {image_link}')

            cursor = con.cursor()
            cursor.execute("SELECT nome_completo, email, cpf_cnpj, telefone FROM usuario WHERE email = ?", (email,))
            usuario = cursor.fetchone()
            cursor.close()

            if not usuario:
                return jsonify({"erro": "Usuário não encontrado"}), 404

            nome_usuario, email_usuario, cpf_usuario, telefone_usuario = usuario

            dados_user = {
                "nome": nome_usuario,
                "email": email_usuario,
                "cpf": cpf_usuario,
                "telefone": telefone_usuario,
                "qrcode_url": image_link,
                "valor": valor
            }

            enviar_email_qrcode(email, dados_user, nome_usuario, payload_completo)

            return send_file(caminho_arquivo, mimetype='image/png', as_attachment=True, download_name=nome_arquivo)
        else:
            print(f' Erro no upload! Código: {response.status_code}')
            print(response.text)

    except Exception as e:
        return jsonify({"erro": f"Ocorreu um erro internosse: {str(e)}"}), 500