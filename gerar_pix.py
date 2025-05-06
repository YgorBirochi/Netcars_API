from flask import Flask, send_file, jsonify, request, render_template
from main import app, con, senha_app_email, senha_secreta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from threading import Thread
from datetime import datetime, timedelta
from flask_apscheduler import APScheduler
import os
import crcmod
import qrcode
import smtplib
import jwt
import requests

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)

def Buscar_Usuario_Devedor():
    with app.app_context():
        cur = con.cursor()

        # Buscar dados da empresa
        cur.execute("SELECT cg.RAZAO_SOCIAL, cg.CHAVE_PIX, cg.CIDADE FROM CONFIG_GARAGEM cg")
        empresa = cur.fetchone()
        razao_social, chave_pix, cidade = empresa

        # Buscar usuários devedores
        cur.execute("""
            SELECT u.ID_USUARIO,
                   fp.VALOR_PARCELA,
                   u.EMAIL,
                   u.NOME_COMPLETO,
                   fp.ID_FINANCIAMENTO,
                   fp.ID_FINANCIAMENTO_PARCELA
            FROM FINANCIAMENTO_PARCELA fp
            LEFT JOIN FINANCIAMENTO f ON f.ID_FINANCIAMENTO = fp.ID_FINANCIAMENTO 
            LEFT JOIN USUARIO u ON u.ID_USUARIO = f.ID_USUARIO 
            WHERE fp.DATA_VENCIMENTO >= CURRENT_DATE + 3 
            and fp.DATA_VENCIMENTO <= CURRENT_DATE + 35  
              AND fp.DATA_PAGAMENTO IS NULL
              AND COALESCE(fp.LEMBRETE, 0) = 0
        """)
        devedores = cur.fetchall()

        # Atualizar lembretes
        for row in devedores:
            id_usuario, valor, email, nome_completo, id_financiamento, id_parcela = row
            cur.execute("""
                UPDATE FINANCIAMENTO_PARCELA 
                SET LEMBRETE = 1 
                WHERE ID_FINANCIAMENTO = ? AND ID_FINANCIAMENTO_PARCELA = ?
            """, (id_financiamento, id_parcela))

        con.commit()

        # Enviar lembretes
        for row in devedores:
            id_usuario, valor, email, nome_completo, _, _ = row
            try:
                payload_completo, link = gerar_pix_funcao(razao_social, valor, chave_pix, cidade)
                data_envio = datetime.now()
                data_limite_str = (data_envio + timedelta(days=1)).strftime("%d/%m/%Y")

                context = {
                    "nome_usuario": nome_completo,
                    "email_destinatario": email,
                    "dados_user": {"nome": nome_completo, "email": email, "qrcode_url": link, "valor": valor},
                    "payload_completo": payload_completo,
                    "data_limite_str": data_limite_str,
                    "endereco_concessionaria": "Av. Exemplo, 1234 - Centro, Cidade Fictícia",
                    "ano": datetime.now().year
                }

                enviar_email_qrcode(
                    to=email,
                    subject="Lembrete de pagamento - NetCars",
                    template="email_lembrete.html",
                    context=context
                )

                print(f"Lembrete enviado para {email} (ID do usuário: {id_usuario})")
            except Exception as e:
                print(f"Erro ao processar usuário {id_usuario}: {e}")

        cur.close()

scheduler.add_job(
    id='BuscarUsuarioDevedor',
    func=Buscar_Usuario_Devedor,
    trigger='interval',
    minutes=1440
)
scheduler.start()

def gerar_pix_funcao(nome: str, valor, chave_pix: str, cidade: str):

    # Validação de parâmetros
    if not nome or not valor or not chave_pix or not cidade:
        raise ValueError("Nome, valor, chave_pix e cidade são obrigatórios")

    # Formatação dos campos
    valor_str = f"{float(valor):.2f}"
    nome = nome[:25]
    cidade = cidade[:15]

    # Montagem do payload PIX (TLV + CRC)
    merchant_info = format_tlv("00", "br.gov.bcb.pix") + format_tlv("01", chave_pix)
    campo_26 = format_tlv("26", merchant_info)
    payload_sem_crc = (
        "000201"
        "010212"
        + campo_26
        + "52040000"
        + "5303986"
        + format_tlv("54", valor_str)
        + "5802BR"
        + format_tlv("59", nome)
        + format_tlv("60", cidade)
        + format_tlv("62", format_tlv("05", "***"))
        + "6304"
    )
    crc = calcula_crc16(payload_sem_crc)
    payload_completo = payload_sem_crc + crc

    # Geração do QR Code
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(payload_completo)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Salvamento local
    pasta = os.path.join(os.getcwd(), "upload", "qrcodes")
    os.makedirs(pasta, exist_ok=True)
    existentes = [f for f in os.listdir(pasta) if f.startswith("pix_") and f.endswith(".png")]
    nums = [int(f.replace("pix_", "").replace(".png", "")) for f in existentes if f.replace("pix_", "").replace(".png", "").isdigit()]
    prox = (max(nums) if nums else 0) + 1
    nome_arquivo = f"pix_{prox}.png"
    caminho = os.path.join(pasta, nome_arquivo)
    img.save(caminho)

    client_id = '2b7b62f0f313a32'

    # Upload para Imgur
    headers = {'Authorization': f'Client-ID {client_id}'}
    with open(caminho, 'rb') as f_img:
        resp = requests.post(
            'https://api.imgur.com/3/image',
            headers=headers,
            data={'type': 'image', 'title': 'Pix', 'description': 'QR Code PIX'},
            files={'image': f_img}
        )
    if resp.status_code != 200:
        raise ConnectionError(f"Erro no upload Imgur: {resp.status_code}")
    link = resp.json().get('data', {}).get('link')

    return payload_completo, link


def enviar_email_qrcode(to: str, subject: str, template: str, context: dict):
    remetente = 'netcars.contato@gmail.com'
    senha = senha_app_email
    servidor_smtp = 'smtp.gmail.com'
    porta_smtp = 465

    corpo = render_template(template, **context)

    # Monta a mensagem com o corpo já fornecido
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(corpo, 'html'))

    def task_envio():
        try:
            server = smtplib.SMTP_SSL(servidor_smtp, porta_smtp, timeout=60)
            server.login(remetente, senha)
            server.sendmail(remetente, to, msg.as_string())
            server.quit()
            print(f"E-mail enviado para {to}")
        except Exception as err:
            print(f"Erro ao enviar e-mail para {to}: {err}")

    Thread(target=task_envio, daemon=True).start()


def calcula_crc16(payload):
    crc16 = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, rev=False)
    crc = crc16(payload.encode('utf-8'))
    return f"{crc:04X}"

def format_tlv(id, value):
    return f"{id}{len(value):02d}{value}"

def remover_bearer(token):
    if token.startswith('Bearer '):
        return token[len('Bearer '):]
    else:
        return token


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
        if not data or 'tipo_veic' not in data or 'id_veic' not in data:
            return jsonify({"error": "Dados incompletos."}), 400

        cursor = con.cursor()

        tipo_veic = data.get('tipo_veic')
        id_veic = data.get('id_veic')

        if tipo_veic == 1:
            cursor.execute('SELECT PRECO_VENDA FROM CARROS WHERE ID_CARRO = ?', (id_veic,))
        elif tipo_veic == 2:
            cursor.execute('SELECT PRECO_VENDA FROM MOTOS WHERE ID_MOTO = ?', (id_veic,))
        else:
            return jsonify({
                'error': 'Tipo de veículo inválido.'
            }), 400

        resposta_veic = cursor.fetchone()

        if not resposta_veic:
            return jsonify({'error': 'Veículo não encontrado.'})

        valor = float(resposta_veic[0])

        cursor.execute("SELECT cg.RAZAO_SOCIAL, cg.CHAVE_PIX, cg.CIDADE FROM CONFIG_GARAGEM cg")
        resultado = cursor.fetchone()
        cursor.close()

        if not resultado:
            return jsonify({"erro": "Chave pix não encontrada"}), 404

        nome, chave_pix, cidade = resultado
        payload, link = gerar_pix_funcao(nome, valor, chave_pix, cidade)

        cursor = con.cursor()
        cursor.execute("SELECT nome_completo, email, cpf_cnpj, telefone FROM usuario WHERE email = ?", (email,))
        usuario = cursor.fetchone()
        cursor.close()

        if not usuario:
            return jsonify({"erro": "Usuário não encontrado"}), 404

        nome_usuario, email_usuario, cpf_usuario, telefone_usuario = usuario
        data_envio = datetime.now()
        data_limite = data_envio + timedelta(days=1)
        data_limite_str = data_limite.strftime("%d/%m/%Y")

        context = {
            'nome_usuario': nome_usuario,
            'email_destinatario': email_usuario,
            'dados_user': {
                'nome': nome_usuario,
                'email': email_usuario,
                'cpf': cpf_usuario,
                'telefone': telefone_usuario,
                'qrcode_url': link,
                'valor': f"{valor:.2f}"
            },
            'payload_completo': payload,
            'data_limite_str': data_limite_str,
            'endereco_concessionaria': "Av. Exemplo, 1234 - Centro, Cidade Fictícia",
            'ano': datetime.now().year
        }

        enviar_email_qrcode(email, "NetCars - Confirmação de Pagamento",'email_pix.html',context )

        caminho = os.path.join(os.getcwd(), "upload", "qrcodes",
                               os.listdir(os.path.join(os.getcwd(), "upload", "qrcodes"))[-1])
        return send_file(caminho, mimetype='image/png', as_attachment=True, download_name=os.path.basename(caminho))

    except Exception as e:
        return jsonify({"erro": f"Ocorreu um erro interno: {str(e)}"}), 500