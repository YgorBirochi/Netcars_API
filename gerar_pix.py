from flask import Flask, send_file, jsonify, request
import qrcode
from io import BytesIO
import crcmod
from datetime import datetime
from main import app, con
import os
from PIL import Image



def calcula_crc16(payload):
    crc16 = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, rev=False)
    crc = crc16(payload.encode('utf-8'))
    return f"{crc:04X}"


def format_tlv(id, value):
    return f"{id}{len(value):02d}{value}"


@app.route('/gerar_pix', methods=['POST'])
def gerar_pix():
    try:
        data = request.get_json()

        if not data or 'valor' not in data:
            return jsonify({"erro": "O valor do PIX é obrigatório."}), 400

        valor = f"{float(data['valor']):.2f}"

        cursor = con.cursor()
        cursor.execute("SELECT cg.RAZAO_SOCIAL, cg.CHAVE_PIX, cg.CIDADE FROM CONFIG_GARAGEM cg ")

        resultado = cursor.fetchone()
        cursor.close()

        if not resultado:
            return jsonify({"erro": f"Chave PIX não encontrada"}), 404

        nome, chave_pix, cidade = resultado
        nome = nome[:25] if nome else "Recebedor PIX"
        cidade = cidade[:15] if cidade else "Cidade"

        # Monta o campo 26 (Merchant Account Information) corretamente com TLVs internos
        merchant_account_info = (
            format_tlv("00", "br.gov.bcb.pix") +  # GUI do Banco Central
            format_tlv("01", chave_pix)           # Chave PIX
            # Pode adicionar outros campos como "02" para descrição, se quiser
        )
        campo_26 = format_tlv("26", merchant_account_info)

        payload_sem_crc = (
            "000201" +                     # Payload Format Indicator
            "010212" +                     # Point of Initiation Method
            campo_26 +                     # Merchant Account Information
            "52040000" +                   # Merchant Category Code
            "5303986" +                    # Currency - 986 = BRL
            format_tlv("54", valor) +      # Transaction amount
            "5802BR" +                     # Country Code
            format_tlv("59", nome) +       # Merchant Name
            format_tlv("60", cidade) +     # Merchant City
            format_tlv("62", format_tlv("05", "***")) +  # Additional data (TXID)
            "6304"                         # CRC placeholder
        )

        crc = calcula_crc16(payload_sem_crc)
        payload_completo = payload_sem_crc + crc

        qr = qrcode.make(payload_completo)

        pasta_uploads = os.path.join("static/uploads", "qrcode")
        os.makedirs(pasta_uploads, exist_ok=True)  # Cria a pasta se não existir

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        nome_arquivo = f"pix.png"
        caminho_arquivo = os.path.join(pasta_uploads, nome_arquivo)

        qr.save(caminho_arquivo)  # Salva o QR Code no disco

        # img_io = BytesIO()
        # qr.save(img_io, 'PNG')
        # img_io.seek(0)

        # return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='pix_qrcode.png')
        return send_file(caminho_arquivo, mimetype='image/png', as_attachment=True, download_name=nome_arquivo)
    except Exception as e:
        return jsonify({"erro": f"Ocorreu um erro interno: {str(e)}"}), 500
