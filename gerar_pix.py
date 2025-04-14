from flask import Flask, send_file, jsonify, request
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from io import BytesIO
import crcmod
from datetime import datetime
from main import app, con
import os
from PIL import Image
import barcode
from barcode.writer import ImageWriter


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

        return send_file(caminho_arquivo, mimetype='image/png', as_attachment=True, download_name=nome_arquivo)
    except Exception as e:
        return jsonify({"erro": f"Ocorreu um erro interno: {str(e)}"}), 500