<!--
SPDX-License-Identifier: Apache-2.0
Autor/desenvolvedor: Elizandro Pacheco — NextHop Solutions® (https://nexthop.solutions/).
Licença e atribuições: consulte LICENSE e NOTICE na raiz do repositório.
-->

# nxt-netflow-stack (NextHop Flow Stack)

> **Camada institucional**: `nexthop-dev-standards` — validado contra a **vX.Y.Z**.

Stack Docker Compose de NetFlow para provedores (Elasticsearch, Kibana, Filebeat e Grafana),
pública sob Apache-2.0, single-node para laboratório e testes locais (`README.md`).

<!-- nexthop:inicio · gerado da camada v9.5.0 por tools/sync-agents-md.mjs — não edite dentro do bloco -->

## Camada NextHop — contrato de entrada

Este projeto segue a camada institucional `nexthop-dev-standards`. Este bloco é gerado por ela:
não edite dentro dele, porque o texto do projeto fica fora. O porquê de cada regra está no
`docs/_meta/delegacao.md` da camada.

**A regra:** faça o trabalho, e no menor tempo. Chame um especialista quando o julgamento dele
valer o que custa — checklist de domínio que você não tem, ou revisão independente como
controle — e reparta em subagentes paralelos quando a tarefa se divide em partes
independentes. Não há designação obrigatória, e agente não compra o que a máquina já mede.

### Onde está o resto da camada

| Ferramenta | Como chegar |
|---|---|
| Claude Code | plugin `nexthop@nexthop`: comandos `/nexthop:<intenção>`, especialistas `nexthop:<nome>` |
| Codex, Copilot, Cursor, Gemini | skills em `~/.agents/skills`: comece por `nexthop-camada`; cada intenção é `nexthop-comando-<intenção>` |

Intenções: `gates` (primeiro, sem agente), `entrega`, `revisar`, `visual`, `design`, `marca`,
`seguranca`, `investigar` e `soltar`. Sem a camada instalada, valem este bloco e a CI do projeto.

### A máquina antes do agente

Rode a intenção `gates` antes de pedir julgamento: classe de risco do diff (`classify-diff`),
suíte do projeto e varredura de segredo (`audit-scan`). Classe C é recomendação medida de
revisão de segurança, não ordem. Pedido vago, relato ("deu erro"), solução pronta sem o problema
ou sem critério de aceite vai primeiro ao `analista-requisitos`; tarefa grande que cruza
domínios, ao `arquiteto-software`.

### Velocidade: paralelo, sem sobreposição

Velocidade é prioridade: o que não depende de outro resultado roda ao mesmo tempo.

- **Reparta antes de executar** e dispare a leva inteira de uma vez: várias chamadas `Agent` na
  mesma mensagem (Claude Code), agentes em paralelo (Codex) ou comandos em segundo plano.
- **Cada designação nomeia os caminhos que escreve**, sem cruzamento; arquivo comum (lock,
  `CHANGELOG`, rota, índice) tem um dono só ou fica para a sessão principal, depois da leva.
- **Só espera quem depende.** Leitura e pesquisa podem se sobrepor; escrita, nunca. Subagente
  não abre subagente: quem reparte e integra é a sessão principal.

### Obrigatórios

Cada um existe porque um incidente aconteceu.

- **Commit, push, tag e instalação de dependência são da sessão principal**, por decisão humana
  para aquela execução e aquele escopo. Subagente não faz nenhum dos quatro.
- **Fronteira de repositório:** trabalhe só no projeto em que a sessão abriu; os outros são
  leitura. Escrever em outro exige pedido que nomeie o projeto e a ação.
- **Duas sessões no mesmo repositório usam worktrees próprios.** Nunca `stash`, `checkout`,
  `reset` ou `restore` em árvore que não é sua.
- **Nunca `rm -rf` em diretório compartilhado** (raiz de scratchpad, `/tmp`): remova só o que
  você criou, por caminho nomeado.
- **Dois agentes da mesma leva nunca editam o mesmo arquivo**, e cada um trabalha na própria
  árvore.
- **Documentação da versão instalada antes de escrever contra API de framework:** Laravel e
  pacote PHP pelo `SearchDocs` do Boost; o resto pelo Context7. Sem resposta, escreva "não
  confirmado na documentação".
- **Decisão de negócio, custo, risco jurídico ou fiscal volta ao humano.**

### Stack

A camada presume Laravel + Inertia + React + Tailwind v4. Confira `composer.json` e
`package.json` antes de aplicar prescrição técnica dela; fora desse stack, valem só as partes
agnósticas (segurança OWASP, acessibilidade, SEO, i18n, performance, git e revisão). Camada
institucional própria do repositório vence esta.

### Fatos deste projeto

Stack, portas, locales e tenancy variam. Leia o overlay do projeto quando existir: no Claude
Code ele entra sozinho; nas outras ferramentas, pela skill `nexthop-projeto-<slug>`.
Sem overlay, não bloqueia: levante do checkout (manifests, locks, CI, `docs/`) e registre de
onde veio cada fato.

### Este arquivo

É o único arquivo de instrução do projeto: sem `CLAUDE.md` (exceção: `@AGENTS.md` mais instrução
só do Claude), sem `@import`, até 200 linhas e 16 KiB. Fora deste bloco, o texto é do projeto.
A linha de versão validada é escrita por humano, no PR em que o projeto for conferido contra a
camada nova. Em conflito, regra da camada vence regra do projeto; para fato (versão, porta),
vale o que foi medido no projeto; exceção a regra mora em ADR.

<!-- nexthop:fim -->

## Produto

Fluxo (`README.md`, *Arquitetura e arquivos*): equipamento → NetFlow/IPFIX em UDP/2055 → Filebeat
(módulo NetFlow) → Elasticsearch; Grafana consulta `filebeat-*` e Kibana explora o mesmo dado.

| Arquivo | Responsabilidade |
|---|---|
| `docker-compose.yaml` | Serviços, versões, portas, rede e volumes |
| `env.example` | Modelo sem senhas; o `.env` real fica fora do git |
| `filebeat.yml` | Módulo NetFlow, saída e instalação da política ILM |
| `elasticsearch/ilm-policy.json` | Rollover e exclusão automática dos índices |
| `grafana/provisioning/`, `template-grafana.json` | Datasource e dashboard provisionados |
| `scripts/smoke-test.py` | Teste local de ingestão e consulta |

## Comandos

```bash
docker compose config -q && docker compose up -d && docker compose ps -a   # subir ou aplicar mudança
python3 scripts/smoke-test.py                                             # teste de ponta a ponta
docker compose up -d --force-recreate filebeat                            # reaplicar a política ILM
```

O `.env` se gera pelo script Python do *Quick start* do `README.md`, que recusa sobrescrever um
existente. `docker compose restart` não aplica mudança de variável: use `up -d`.

## Fatos deste projeto

- **Versões fixadas no Compose** (verificadas em 01/10/2026, `README.md`): Elasticsearch, Kibana e
  Filebeat 9.5.4 (sempre na mesma versão), Grafana 13.2.3, curl 8.22.0.
- **Portas**: Elasticsearch 9200, Kibana 5601 e Grafana 3000 em `127.0.0.1` (`HTTP_BIND_ADDRESS`);
  Filebeat UDP/2055 em todas as interfaces.
- **Sem CI** no repositório; o teste é o `scripts/smoke-test.py`, que não valida exportador físico,
  v9/IPFIX, carga sustentada nem perda de pacote.
- Os arquivos de texto levam cabeçalho SPDX `Apache-2.0` com autor e data de modificação (ex.: `README.md`);
  `LICENSE`, `LICENSE.pt-BR.md` e `NOTICE` na raiz.
- Fora do stack Laravel + Inertia da camada: valem só as partes agnósticas. Sem overlay deste
  projeto na camada; fatos levantados do checkout.

## Invariantes e armadilhas

- **A retenção apaga dado de forma definitiva**: `delete.min_age` 7d contado do rollover (1d ou 5gb),
  ou seja, cerca de 7 a 8 dias. O JSON versionado é a fonte (`setup.ilm.overwrite: true`); mudança
  feita só pelo Kibana é sobrescrita (`README.md`, *Persistência, retenção e atualização*).
- **Não monte volume do Elastic 8.12.2 no 9.5.4**; os volumes atuais têm nomes novos e a atualização
  segue o caminho oficial da Elastic.
- O Compose recusa senha vazia; `KIBANA_SYSTEM_PASSWORD` só aceita letras, números, `_` e `-`.
- O Elasticsearch tem limite de 1 GB no Compose e heap de 512 MB: subiu o heap, suba o limite.
