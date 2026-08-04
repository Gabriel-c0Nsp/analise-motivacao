"""Sem configuração de teste.

Existe para que o pytest coloque a raiz do repositório no sys.path e o pacote
survey seja importável ao rodar `pytest` direto, sem `python -m pytest`. O
arquivo precisa ficar aqui: o pytest insere o diretório do conftest, então um
conftest.py dentro de tests/ colocaria tests/ no caminho, e não a raiz.
"""
