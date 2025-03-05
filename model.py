import fdb

class Usuario:
    def __init__(self, id_usuario, nome_completo, data_nascimento, cpf_cnpj, telefone, email, senha_hash, endereco, data_cadastro, atualizado_em, adm, tipo_usuario):
        self.id_usuario = id_usuario
        self.nome_completo = nome_completo
        self.data_nascimento = data_nascimento
        self.cpf_cnpj = cpf_cnpj
        self.telefone = telefone
        self.email = email
        self.senha_hash = senha_hash
        self.data_cadastro = data_cadastro
        self.atualizado_em = atualizado_em
        self.tipo_usuario = tipo_usuario


class Carro:
    def __init__(self, id_carro, marca, modelo, ano_modelo, ano_fabricacao, versao, cor, cambio, combustivel, categoria, quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, criado_em, atualizado_em):
        self.id_carro = id_carro
        self.marca = marca
        self.modelo = modelo
        self.ano_modelo = ano_modelo
        self.ano_fabricacao = ano_fabricacao
        self.versao = versao
        self.cor = cor
        self.cambio = cambio
        self.combustivel = combustivel
        self.categoria = categoria
        self.quilometragem = quilometragem
        self.estado = estado
        self.cidade = cidade
        self.preco_compra = preco_compra
        self.preco_venda = preco_venda
        self.licenciado = licenciado
        self.criado_em = criado_em
        self.atualizado_em = atualizado_em
        self.placa = placa


class Moto:
    def __init__(self, id_moto, marca, modelo, ano_modelo, ano_fabricacao, estilo, cor, marchas, partida, tipo_motor, cilindradas, freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem, preco_compra, preco_venda, licenciado, criado_em, atualizado_em):
        self.id_moto = id_moto
        self.marca = marca
        self.modelo = modelo
        self.ano_modelo = ano_modelo
        self.ano_fabricacao = ano_fabricacao
        self.estilo = estilo
        self.cor = cor
        self.marchas = marchas
        self.partida = partida
        self.tipo_motor = tipo_motor
        self.cilindradas = cilindradas
        self.freio_dianteiro_traseiro = freio_dianteiro_traseiro
        self.refrigeracao = refrigeracao
        self.estado = estado
        self.cidade = cidade
        self.quilometragem = quilometragem
        self.preco_compra = preco_compra
        self.preco_venda = preco_venda
        self.licenciado = licenciado
        self.criado_em = criado_em
        self.atualizado_em = atualizado_em
        self.placa = placa


class DocumentacaoVeiculos:
    def __init__(self, id_documentacao, id_carro, id_moto, renavam, placa, quitacao_debitos, criado_em, atualizado_em):
        self.id_documentacao = id_documentacao
        self.id_carro = id_carro
        self.id_moto = id_moto
        self.renavam = renavam
        self.placa = placa
        self.quitacao_debitos = quitacao_debitos
        self.criado_em = criado_em
        self.atualizado_em = atualizado_em


class VendaCompra:
    def __init__(self, id_venda, id_usuario, id_carro, id_moto, valor_total, forma_pagamento, entrada, parcelamento, instituicao_financeira, valor_parcelas, status, data_venda, criado_em, atualizado_em):
        self.id_venda = id_venda
        self.id_usuario = id_usuario
        self.id_carro = id_carro
        self.id_moto = id_moto
        self.valor_total = valor_total
        self.forma_pagamento = forma_pagamento
        self.entrada = entrada
        self.parcelamento = parcelamento
        self.instituicao_financeira = instituicao_financeira
        self.valor_parcelas = valor_parcelas
        self.status = status
        self.data_venda = data_venda
        self.criado_em = criado_em
        self.atualizado_em = atualizado_em
