from flask import Flask, send_file
from main import app, con
from fpdf import FPDF

@app.route('/relatorio/carros', methods=['GET'])
def criar_pdf_carro():

    cursor = con.cursor()
    cursor.execute("SELECT id_carro, marca, modelo, ano_modelo, ano-fabricacao, versao, cor, cambio, combustivel, categoria, quilometragem, estado, cidade, preco-compra, preco_venda, licenciado FROM carros")
    carros = cursor.fethcall()
    cursor.close()

    #Criação do PDF:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Informações carro", ln=True, align='C')

    #Adicionando uma Linha Separadora:
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Inserindo os Dados dos Livros:
    pdf.set_font("Arial", size=12)
    for carro in carros:
        pdf.cell(200, 10, f"ID: {carro[0]} - {carro[1]} - {carro[2]} - {carro[3]} - {carro[4]} - {carro[5]} - {carro[6]} - {carro[7]} - {carro[8]} - {carro[9]} - {carro[10]} - {carro[11]} - {carro[12]} - {carro[13]} - {carro[14]} - {carro[15]} - {carro[16]}", ln=True)

    # Adicionando o Total de Carros Cadastrados:
    pdf_path = "relatorio_carros.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')

@app.route('/relatorio/motos', methods=['GET'])
def criar_pdf_moto():

    cursor = con.cursor()
    cursor.execute("SELECT id_moto, marca, modelo, ano_modelo, ano-fabricacao, estilo, cor, marchas, partida, tipo_motor, cilindradas, freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem, preco_compra, preco_venda, licenciado FROM motos")
    motos = cursor.fethcall()
    cursor.close()

    #Criação do PDF:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Informações moto", ln=True, align='C')

    #Adicionando uma Linha Separadora:
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Inserindo os Dados dos Livros:
    pdf.set_font("Arial", size=12)
    for moto in motos:
        pdf.cell(200, 10, f"ID: {moto[0]} - {moto[1]} - {moto[2]} - {moto[3]} - {moto[4]} - {moto[5]} - {moto[6]} - {moto[7]} - {moto[8]} - {moto[9]} - {moto[10]} - {moto[11]} - {moto[12]} - {moto[13]} - {moto[14]} - {moto[15]} - {moto[16]} - {moto[17]} - {moto[18]} - {moto[19]}", ln=True)

    # Adicionando o Total de Motos Cadastradas:
    pdf_path = "relatorio_motos.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')