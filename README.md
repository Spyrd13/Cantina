# CANTINA TUFI - Sistema de Gestão

**Versão:** 1.0.0  
**Python Mínimo:** 3.11+  
**Última Atualização:** 2024

---

## 📋 Descrição do Projeto

Cantina TUFI é um sistema de gestão integrado para cantinas, desenvolvido com Python e Flet (framework de UI multiplataforma). O sistema oferece controle completo de:

- ✅ Vendas e pedidos
- ✅ Estoque e inventário
- ✅ Gerenciamento de itens/produtos
- ✅ Cadastro de clientes
- ✅ Controle financeiro
- ✅ Histórico de transações e pendurados (com filtro por cliente e data)
- ✅ Relatórios e análises

**Arquitetura:** Três camadas (Repository → Service → View)  
**Database:** SQLite local (`database/cantina.db`)

---

## 🚀 Instalação Rápida

### 1. Pré-requisitos
- Python 3.11 ou superior
- Git (recomendado)
- Windows, Linux ou macOS

### 2. Clonar Repositório
```bash
git clone <url-do-repositorio>
cd TUFI
```

### 3. Criar e Ativar Ambiente Virtual

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 5. Configurar Ambiente (Opcional)

O projeto já vem com `.env.local` configurado. Para customizar:

```bash
# Edite o arquivo .env.local com suas configurações
ENV=development
DATABASE_URL=sqlite:///database/cantina.db
DEBUG=True
LOG_LEVEL=DEBUG
APP_TITLE=Cantina TUFI
APP_VERSION=1.0.0
```

---

## ▶️ Executar a Aplicação

### 1. Ativar Ambiente Virtual (se não estiver)

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 2. Executar

```bash
python main.py
```

Ou usando Flet diretamente:
```bash
flet run main.py
```

A aplicação abrirá em uma janela de desktop. O banco de dados será criado automaticamente.

---

## 📁 Estrutura do Projeto

```
TUFI/
├── main.py                    # Ponto de entrada (com error handling)
├── requirements.txt           # Dependências
├── .env.example              # Template de configuração
├── .env.local                # Configuração local
├── README.md                 # Este arquivo
├── database/
│   └── cantina.db            # SQLite (criado automaticamente)
└── app/
    ├── core/
    │   └── database.py       # Configuração ORM/Logging
    ├── models/               # SQLModel (dados)
    │   ├── cliente.py
    │   ├── financeiro.py
    │   ├── item.py
    │   └── movimentacao.py
    ├── repository/           # Acesso a dados
    │   ├── cliente_repository.py
    │   ├── financeiro_repository.py
    │   ├── item_repository.py
    │   ├── movimentacao_repository.py
    │   └── relatorio_repository.py
    ├── services/             # Lógica de negócio
    │   ├── cliente_services.py
    │   ├── financeiro_services.py
    │   ├── item_services.py
    │   ├── movimentacao_services.py
    │   ├── relatorio_services.py
    │   └── venda_service.py  # Transações completas
    ├── schemas/              # Validação (Pydantic)
    ├── utils/
    │   └── enums.py          # Tipos/Enumerações
    └── views/                # Interface (Flet)
        ├── clientes_view.py
        ├── estoque_view.py
        ├── financeiro_view.py
        ├── historico_view.py  # Pendurados + filtros
        ├── items_view.py
        ├── movimentacoes_view.py
        ├── relatorio_view.py
        └── vendas_view.py     # Transações com cache
```

---

## 🎯 Módulos Principais

### 1. **Vendas**
- Criar novos pedidos/vendas
- Selecionar itens e quantidades
- Definir cliente (opcional)
- Registrar forma de pagamento
- Estoque atualizado automaticamente

### 2. **Estoque**
- Visualizar produtos e quantidades
- Alertas de estoque baixo
- Histórico de movimentações

### 3. **Itens**
- Cadastrar produtos
- Editar informações
- Definir preços

### 4. **Clientes**
- Cadastrar clientes
- Editar dados
- Consultar histórico

### 5. **Financeiro**
- Registrar receitas e despesas
- Acompanhar transações
- Relatórios de fluxo

### 6. **Histórico** ⭐ NOVO
- Vendas completas
- **Pendurados** (vendas não pagas) com filtros:
  - Por cliente
  - Por data (período)
- Movimentações de estoque
- Transações financeiras

### 7. **Relatório**
- Resumos financeiros
- Análises de vendas
- Relatórios customizados

---

## 📊 Tipos Suportados

### Movimentação
- `entrada` - Produto entra no estoque
- `saida` - Produto sai (venda)
- `ajuste` - Correção de estoque
- `perda` - Produto perdido/descartado

### Financeiro
- `receita` - Dinheiro entrando
- `despesa` - Dinheiro saindo

### Pagamento
- `dinheiro` - Dinheiro
- `debito` - Cartão débito
- `credito` - Cartão crédito
- `pix` - PIX/Transferência

---

## 📦 Dependências

| Pacote | Versão | Uso |
|--------|--------|-----|
| flet | 0.24.0 | UI multiplataforma |
| sqlmodel | 0.0.14 | ORM + validação |
| SQLAlchemy | 2.0.23 | Banco de dados |
| pydantic | 2.5.0 | Validação |
| pydantic-settings | 2.1.0 | Configuração |
| python-dotenv | 1.0.0 | Variáveis de ambiente |

Para mais detalhes: [requirements.txt](requirements.txt)

---

## 🔧 Configuração Avançada

### Variáveis de Ambiente (.env.local)

```ini
# Ambiente
ENV=development              # ou 'production'

# Banco de dados
DATABASE_URL=sqlite:///database/cantina.db

# Debug e Logging
DEBUG=True                   # True = logs verbosos, False = production
LOG_LEVEL=DEBUG             # DEBUG, INFO, WARNING, ERROR

# Aplicação
APP_TITLE=Cantina TUFI
APP_VERSION=1.0.0
```

### Debug e Logs

Quando `DEBUG=True`, o SQLAlchemy exibe todas as queries em tempo real:
```sql
BEGIN (implicit)
INSERT INTO item (nome, preco, estoque) VALUES (?, ?, ?)
...
COMMIT
```

Em produção, deixe `DEBUG=False` para melhor performance.

---

## 🆘 Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'flet'"
```bash
# Certifique-se que o venv está ativado
pip install -r requirements.txt
```

### ❌ "Database is locked"
- Feche a aplicação completamente
- Aguarde 1-2 segundos
- Reabra

### ❌ "Erro ao carregar página"
- Verifique `LOG_LEVEL=DEBUG` em `.env.local`
- Verifique se `database/cantina.db` existe
- Reinicie a aplicação

### ❌ Aplicação congela ao abrir
- Configure `DEBUG=False` em `.env.local`
- Reduza o tamanho dos dados/relatórios
- Limpe cache: remova `__pycache__/` e `.flet/`

---

## 🏗️ Arquitetura

### Padrão MVC + Services

```
View (Flet)
    ↓
Service (Lógica)
    ↓
Repository (Dados)
    ↓
Database (SQLite)
```

### Características

✅ **Separação de responsabilidades** - Views não acessam DB direto  
✅ **Transações seguras** - Rollback automático em erros  
✅ **Validação em camadas** - Pydantic + SQLModel  
✅ **Error handling** - Try/except com logging  
✅ **Performance** - Cache em memória para listas grandes  
✅ **Multiplataforma** - Windows, Linux, macOS

---

## ⚙️ Otimizações Implementadas

1. **Caching em vendas_view.py**
   - Items carregados uma vez em memória
   - O(1) lookup em vez de queries do banco

2. **Lazy imports em main.py**
   - Views carregadas sob demanda
   - Inicialização mais rápida

3. **Conditional echo no database.py**
   - Logs de SQL apenas em desenvolvimento
   - Melhor performance em produção

4. **Transações ACID em venda_service.py**
   - Commit/Rollback automático
   - Consistência garantida

---

## 📝 Notas Importantes

1. ⚠️ **Backup**: Faça backup regularmente de `database/cantina.db`
2. ⚠️ **Edição Manual**: Não modifique manualmente a estrutura do banco
3. ⚠️ **Atualizações**: Sempre revise o `.env.local` após atualizações
4. ✅ **Logs**: Mantenha `LOG_LEVEL=INFO` em produção

---

## 📜 Licença

### Termos de Uso (EULA)

1. ✅ Você pode utilizar para fins **pessoais, educacionais** ou adaptação
2. ❌ É proibido **distribuir, copiar, revender** sem autorização
3. ❌ Não reivindicar autoria se derivado deste projeto
4. ⚠️ Sem garantia: o autor **não oferece suporte** ou responsabilidade por danos

---

## 👨‍💻 Desenvolvimento

Desenvolvido com:
- Python 3.11+
- SQLModel/SQLAlchemy
- Flet (UI cross-platform)
- Logging estruturado
- Tratamento robusto de erros

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a seção **Troubleshooting**
2. Ative `DEBUG=True` e consulte os logs
3. Verifique se todas as dependências estão instaladas

---

**Desenvolvido em 2024 - Cantina TUFI**
