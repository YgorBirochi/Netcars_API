from flask import Flask, send_file
from main import app, con
from fpdf import FPDF

def format_currency(value):
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
    formatted = f"{value:,.2f}"  # Exemplo: "2,000.00"
    formatted = formatted.replace(",", "v").replace(".", ",").replace("v", ".")
    return "R$ " + formatted
def format_kilometragem(value):
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
    formatted = f"{value:,.0f}"  # Sem casas decimais
    formatted = formatted.replace(",", "v").replace(".", ",").replace("v", ".")
    return formatted + " km"

@app.route('/relatorio/carros', methods=['GET'])
def criar_pdf_carro():
    cursor = con.cursor()
    cursor.execute("SELECT id_carro, marca, modelo, placa, ano_modelo, ano_fabricacao, versao, cor, renavam, cambio, combustivel, categoria, quilometragem, estado, cidade, preco_compra, preco_venda, licenciado FROM carros")
    carros = cursor.fetchall()
    cursor.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Informações carro", ln=True, align='C')

    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    for carro in carros:
        campos = [
            ("ID", carro[0]),
            ("Marca", carro[1]),
            ("Modelo", carro[2]),
            ("Placa", carro[3]),
            ("Ano Modelo", carro[4]),
            ("Ano Fabricação", carro[5]),
            ("Versão", carro[6]),
            ("Cor", carro[7]),
            ("Renavam", carro[8]),
            ("Câmbio", carro[9]),
            ("Combustível", carro[10]),
            ("Categoria", carro[11]),
            ("Quilometragem", carro[12]),
            ("Estado", carro[13]),
            ("Cidade", carro[14]),
            ("Preço Compra", carro[15]),
            ("Preço Venda", carro[16]),
            ("Licenciado", carro[17])
        ]

        for nome, valor in campos:
            if nome == "Licenciado":
                valor = "Sim" if valor == 1 else "Não"
            elif nome in ["Preço Compra", "Preço Venda"]:
                valor = format_currency(valor)
            elif nome == "Quilometragem":
                valor = format_kilometragem(valor)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(40, 10, f"{nome}:", border=0)
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 10, str(valor), ln=1)
        # Barra separadora após cada veículo
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    pdf_path = "relatorio_carros.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')

@app.route('/relatorio/motos', methods=['GET'])
def criar_pdf_moto():
    cursor = con.cursor()
    cursor.execute("SELECT id_moto, marca, modelo, placa, ano_modelo, ano_fabricacao, categoria, cor, renavam, marchas, partida, tipo_motor, cilindrada, freio_dianteiro_traseiro, refrigeracao, alimentacao, versao, estado, cidade, quilometragem, preco_compra, preco_venda, licenciado FROM motos")
    motos = cursor.fetchall()
    cursor.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Informações moto", ln=True, align='C')

    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    for moto in motos:
        campos = [
            ("ID", moto[0]),
            ("Marca", moto[1]),
            ("Modelo", moto[2]),
            ("Placa", moto[3]),
            ("Ano Modelo", moto[4]),
            ("Ano Fabricação", moto[5]),
            ("Categoria", moto[6]),
            ("Cor", moto[7]),
            ("Renavam", moto[8]),
            ("Marchas", moto[9]),
            ("Partida", moto[10]),
            ("Tipo do Motor", moto[11]),
            ("Cilindradas", moto[12]),
            ("Freio D/T", moto[13]),
            ("Refrigeração", moto[14]),
            ("Alimentação", moto[15]),
            ("Versão", moto[16]),
            ("Estado", moto[17]),
            ("Cidade", moto[18]),
            ("Quilometragem", moto[19]),
            ("Preço de Compra", moto[20]),
            ("Preço de Venda", moto[21]),
            ("Licenciado", moto[22])
        ]
        for nome, valor in campos:
            if nome == "Licenciado":
                valor = "Sim" if valor == 1 else "Não"
            elif nome in ["Preço de Compra", "Preço de Venda"]:
                valor = format_currency(valor)
            elif nome == "Quilometragem":
                valor = format_kilometragem(valor)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(40, 10, f"{nome}:", border=0)
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 10, str(valor), ln=1)
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    pdf_path = "relatorio_motos.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')