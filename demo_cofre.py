"""
Demonstracao rapida do cofre, rodando contra o banco MySQL de verdade.
Uso: python demo_cofre.py
"""
import secrets
import cofre

# nome unico para poder rodar varias vezes sem colidir
nome = "demo_" + secrets.token_hex(3)
senha_mestra = "minhaSenhaMestra"

print(f"1) Criando usuario '{nome}'...")
uid = cofre.criar_usuario(nome, senha_mestra)
print(f"   usuario criado (id={uid})")

print("2) Desbloqueando com a senha CERTA...")
sessao = cofre.desbloquear(nome, senha_mestra)
print("   ->", "desbloqueou OK" if sessao else "FALHOU")

print("3) Desbloqueando com a senha ERRADA...")
erro = cofre.desbloquear(nome, "senhaErrada")
print("   ->", "rejeitou corretamente" if erro is None else "FALHOU (aceitou senha errada!)")

chave = sessao["chave"]
print("4) Adicionando duas senhas...")
cofre.adicionar_entrada(sessao["id_usuario"], chave, "Nubank", "senha-do-banco-123", usuario_servico="guizin")
cofre.adicionar_entrada(sessao["id_usuario"], chave, "Gmail", "outra-senha-456")
print("   adicionadas.")

print("5) Listando e decifrando as entradas:")
for e in cofre.listar_entradas(sessao["id_usuario"], chave):
    print(f"   - {e['titulo']}: {e['senha']}")

print("\nFluxo completo funcionou de ponta a ponta!")
