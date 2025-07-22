# GitHub Recent Clones

## 🔧 Environment Setup

1. Create a `.env` file in the project root.
2. Add your GitHub personal access token:

```env
GH_TOKEN=<your_github_token>
```

3. Install dependecies:
```cmd
pip install requirements.txt
```


Heurística:
**Clones adicionados**

Indexar código completo do commit PRb
Gerar um diff entre PRb e PRm para cada arquivo.java 
Capturar todos os blocos adicionados e removidos
Para cada bloco adicionado que é igual ao bloco removido, remover eles (blocos movidos)

Search blocos de código adicionados


# TODO
- fix collumn: qtd_blocks_removed, qtd_blocks_added
- fix collumn: simian_result_removed
