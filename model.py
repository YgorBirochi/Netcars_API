import fdb

class Usuario:
    def __init__(self, id_usuario, nome_completo, data_nascimento, email, senha_hash, data_cadastro, atualizado_em,
                 ativo, tipo_usuario, telefone, cpf_cnpj, codigo, codigo_criado_em, trocar_senha):

        self.id_usuario = id_usuario
        self.nome_completo = nome_completo
        self.data_nascimento = data_nascimento
        self.email = email
        self.senha_hash = senha_hash
        self.data_cadastro = data_cadastro
        self.atualizado_em = atualizado_em
        self.ativo = ativo
        self.tipo_usuario = tipo_usuario
        self.telefone = telefone
        self.cpf_cnpj = cpf_cnpj
        self.codigo = codigo
        self.codigo_criado_em = codigo_criado_em
        self.trocar_senha = trocar_senha

class Carro:
    def __init__(self, id_carro, marca, modelo, ano_modelo, ano_fabricacao, versao, cor, cambio, combustivel, categoria,
                 quilometragem, estado, cidade, preco_compra, preco_venda, licenciado, criado_em, atualizado_em, placa,
                 ativo, renavam, reservado, reservado_em, id_usuario_reserva):

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
        self.ativo = ativo
        self.renavam = renavam
        self.reservado = reservado
        self.reservado_em = reservado_em
        self.id_usuario_reserva = id_usuario_reserva

class Moto:
    def __init__(self, id_moto, marca, modelo, ano_modelo, ano_fabricacao, categoria, cor, marchas, partida, tipo_motor, cilindrada,
                 freio_dianteiro_traseiro, refrigeracao, estado, cidade, quilometragem, preco_compra, preco_venda, licenciado,
                 criado_em, atualizado_em, placa, ativo, alimentacao, renavam, reservado, reservado_em, id_usuario_reserva):

        self.id_moto = id_moto
        self.marca = marca
        self.modelo = modelo
        self.ano_modelo = ano_modelo
        self.ano_fabricacao = ano_fabricacao
        self.categoria = categoria
        self.cor = cor
        self.marchas = marchas
        self.partida = partida
        self.tipo_motor = tipo_motor
        self.cilindrada = cilindrada
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
        self.ativo = ativo
        self.alimentacao = alimentacao
        self.renavam = renavam
        self.reservado = reservado
        self.reservado_em = reservado_em
        self.id_usuario_reserva = id_usuario_reserva


class ConfigGaragem:
    def __init__(self, id_config_garagem, nome_fantasia, razao_social, chave_pix, cidade, cnpj):

        self.id_config_garagem = id_config_garagem
        self.nome_fantasia = nome_fantasia
        self.razao_social = razao_social
        self.chave_pix = chave_pix
        self.cidade = cidade
        self.cnpj = cnpj

class VendaCompra:
    def __init__(self, id_venda_compra, tipo_venda_compra, valor_total, forma_pagamento, entrada, qnt_parcelas, data_venda_compra,
                 id_usuario, tipo_veiculo, id_veiculo, status, id_financiamento):

        self.id_venda_compra = id_venda_compra
        self.tipo_venda_compra = tipo_venda_compra
        self.valor_total = valor_total
        self.forma_pagamento = forma_pagamento
        self.entrada = entrada
        self.qnt_parcelas = qnt_parcelas
        self.data_venda_compra = data_venda_compra
        self.id_usuario = id_usuario
        self.tipo_veiculo = tipo_veiculo
        self.valor_parcelas = valor_parcelas
        self.id_veiculo = id_veiculo
        self.data_venda = data_venda
        self.status = status
        self.id_financiamento = id_financiamento

class Financiamento:
    def __init__(self, id_financiamento, id_usuario, entrada, qnt_parcelas, tipo_veiculo, id_veiculo, valor_total):

        self.id_financiamento = id_financiamento
        self.id_usuario = id_usuario
        self.entrada = entrada
        self.qnt_parcelas = qnt_parcelas
        self.tipo_veiculo = tipo_veiculo
        self.id_veiculo = id_veiculo
        self.valor_total = valor_total

class FinanciamentoParcela:
    def __init__(self, id_financiamento, id_financiamento_parcela, num_parcela, valor_parcela, valor_parcela_amortizada,
                 data_vencimento, data_pagamento, status):

        self.id_financiamento = id_financiamento
        self.id_financiamento_parcela = id_financiamento_parcela
        self.num_parcela = num_parcela
        self.valor_parcela = valor_parcela
        self.valor_parcela_amortizada = valor_parcela_amortizada
        self.data_vencimento = data_vencimento
        self.data_pagamento = data_pagamento
        self.status = status

class Manutencao:
    def __init__(self, id_manutencao, id_veiculo, data_manutencao, observacao, valor_total, tipo_veiculo, ativo):

        self.id_manutencao = id_manutencao
        self.id_veiculo = id_veiculo
        self.data_manutencao = data_manutencao
        self.observacao = observacao
        self.valor_total = valor_total
        self.tipo_veiculo = tipo_veiculo
        self.ativo = ativo

class ManutencaoServicos:
    def __init__(self, id_manutencao_servicos, id_manutencao, id_servicos, quantidade, valor_total_item):

        self.id_manutencao_servicos = id_manutencao_servicos
        self.id_manutencao = id_manutencao
        self.id_servicos = id_servicos
        self.quantidade = quantidade
        self.valor_total_item = valor_total_item

class Servicos:
    def __init__(self, id_servicos, descricao, valor, ativo):

        self.id_servicos = id_servicos
        self.descricao = descricao
        self.valor = valor
        self.ativo = ativo

class ReceitaDespesa:
    def __init__(self, id_receita_despesa, tipo, valor, data_receita_despesa, descricao, id_origem, tabela_origem):

        self.id_receita_despesa = id_receita_despesa
        self.tipo = tipo
        self.valor = valor
        self.data_receita_despesa = data_receita_despesa
        self.descricao = descricao
        self.id_origem = id_origem
        self.tabela_origem = tabela_origem