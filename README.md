<div align="center">

# NextHop Flow Stack

**Visibilidade de tráfego NetFlow para provedores de Internet.**

Elasticsearch · Kibana · Filebeat · Grafana

[![Licença Apache 2.0](https://img.shields.io/github/license/nexthopsolutions/nxt-netflow-stack?style=flat-square&color=2563eb)](./LICENSE)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](./docker-compose.yaml)
[![GitHub Stars](https://img.shields.io/github/stars/nexthopsolutions/nxt-netflow-stack?style=flat-square&color=eab308)](https://github.com/nexthopsolutions/nxt-netflow-stack/stargazers)

[**Começar agora**](#quick-start) · [Dashboard](./template-grafana.json) · [Configuração](#configuracao-env) · [Solução de problemas](#troubleshooting)

</div>

---

Stack de **NetFlow para ISPs**, com **Elasticsearch, Kibana, Filebeat e Grafana**, desenvolvida pela **NextHop Solutions®**, através de seu CEO **Elizandro Pacheco**, como contribuição para a comunidade.

Preparada para apresentação na [15ª Semana de Infraestrutura da Internet no Brasil](https://semanainfra.nic.br/) e no [GTER/GTS](https://gtergts.nic.br/).

Receba fluxos dos seus equipamentos, explore eventos no Kibana e visualize o tráfego em um dashboard Grafana provisionado automaticamente.

> [!TIP]
> **O projeto ajudou você? Dê uma estrela ⭐** no [repositório](https://github.com/nexthopsolutions/nxt-netflow-stack), pelo botão **Star** no topo da página. Isso ajuda outros profissionais a encontrar a solução e apoia sua divulgação na comunidade.

> [!IMPORTANT]
> Esta configuração é uma base **single-node para laboratório e testes locais**. Para produção, dimensione recursos, retenção, autenticação, TLS e backups conforme seu ambiente.

## 📌 Sumário

- [🚀 Quick start](#quick-start)
- [🧱 Componentes e versões](#componentes)
- [🧭 Portas e endpoints](#portas-e-endpoints)
- [🗺️ Arquitetura e arquivos](#arquitetura)
- [✅ Pré-requisitos](#pre-requisitos)
- [🔧 Configuração e credenciais](#configuracao-env)
- [📊 Grafana e Kibana](#interfaces)
- [📡 Exportadores NetFlow](#exportadores-netflow)
- [🗃️ Persistência, retenção e atualização](#persistencia-e-dados)
- [🧰 Operação e testes](#operacao)
- [🔐 Segurança em produção](#seguranca-producao)
- [🧯 Troubleshooting](#troubleshooting)
- [📚 Materiais](#materiais)
- [🤝 Apoiadores](#apoiadores)
- [📫 Contato](#contato)
- [📄 Licença](#licenca)

<a id="quick-start"></a>
## 🚀 Quick start

Execute os comandos na pasta do repositório, com o Docker em execução. Consulte os [pré-requisitos](#pre-requisitos) antes de iniciar.

### 1. Obtenha o projeto

```bash
git clone https://github.com/nexthopsolutions/nxt-netflow-stack.git
cd nxt-netflow-stack
```

Se você já tem o checkout, use a pasta existente.

### 2. Gere o `.env` com senhas exclusivas

O comando abaixo usa Python 3, copia as configurações de `env.example` e preenche as três senhas. Ele **recusa sobrescrever um `.env` existente**.

```bash
python3 - <<'PY'
from pathlib import Path
import os
import secrets

text = Path('env.example').read_text()
for key in ('ELASTIC_PASSWORD', 'KIBANA_SYSTEM_PASSWORD', 'GRAFANA_ADMIN_PASSWORD'):
    text = text.replace(key + '=\n', key + '=' + secrets.token_urlsafe(32) + '\n')
fd = os.open('.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as output:
    output.write(text)
print('.env criado com senhas exclusivas.')
PY
```

Se preferir configurar manualmente, copie `env.example` para `.env` e preencha os campos de senha vazios antes de subir. Não reutilize senhas publicadas em versões antigas do exemplo.

### 3. Valide e inicie

```bash
docker compose config -q
docker compose pull
docker compose up -d
docker compose ps -a
```

A primeira inicialização pode levar alguns minutos. `setup_kibana_system_password` deve terminar com **Exited (0)**; os outros quatro serviços devem permanecer em execução. `up -d` sozinho não comprova que todas as aplicações estão prontas.

### 4. Acesse e teste

- **[Grafana](http://localhost:3000)**: usuário `admin` (ou `GRAFANA_ADMIN_USER`) e senha `GRAFANA_ADMIN_PASSWORD` do `.env`.
- **[Kibana](http://localhost:5601)**: usuário `elastic` e senha `ELASTIC_PASSWORD` do `.env`.

```bash
python3 scripts/smoke-test.py
```

O teste gera um evento sintético; para receber tráfego real, configure os equipamentos para exportar para **IP do host Docker, UDP/2055**. Veja [exportadores](#exportadores-netflow).

<a id="componentes"></a>
## 🧱 Componentes e versões

Versões fixadas no Compose e verificadas em **01/10/2026**:

| Componente | Versão | Função |
|---|---|---|
| Elasticsearch | 9.5.4 | Armazenamento e busca |
| Kibana | 9.5.4 | Exploração dos eventos |
| Filebeat | 9.5.4 | Coleta e decodificação de NetFlow/IPFIX |
| Grafana | 13.2.3 | Visualização dos dados |
| curl | 8.22.0 | Inicialização da senha de `kibana_system` |

Fontes oficiais: [Elasticsearch](https://www.elastic.co/downloads/elasticsearch/), [Kibana](https://www.elastic.co/downloads/kibana), [Filebeat](https://www.elastic.co/downloads/beats/filebeat), [Grafana](https://grafana.com/grafana/download) e [curl](https://hub.docker.com/r/curlimages/curl/tags).

As tags são explícitas: `docker compose pull` baixa as versões declaradas, sem trocar automaticamente para uma versão futura. Mantenha os três componentes Elastic na mesma versão ao atualizar esta stack.

<a id="portas-e-endpoints"></a>
## 🧭 Portas e endpoints

| Serviço | Porta no host | Publicação padrão |
|---|---|---|
| Elasticsearch | TCP/9200 | `127.0.0.1` |
| Kibana | TCP/5601 | `127.0.0.1` |
| Grafana | TCP/3000 | `127.0.0.1` |
| Filebeat NetFlow | UDP/2055 | Todas as interfaces disponíveis |

Para acessar as interfaces HTTP a partir de outra máquina, configure `HTTP_BIND_ADDRESS` com o IP da interface do host desejada e execute `docker compose up -d`. `0.0.0.0` publica em todas as interfaces IPv4; restrinja o acesso por firewall/VPN. Esse ajuste **não altera** a publicação UDP.

O teste automatizado usa `127.0.0.1` e as portas padrão. Execute-o com a publicação HTTP padrão ou em `0.0.0.0`. Se publicar exclusivamente em um IP de LAN, o teste precisará ser adaptado.

<a id="arquitetura"></a>
## 🗺️ Arquitetura e arquivos

```text
Roteador / BRAS / switch
        │ NetFlow / IPFIX — UDP/2055
        ▼
     Filebeat ──HTTP autenticado──► Elasticsearch
                                        ▲
                                        │ consultas
                                 Kibana / Grafana
```

O módulo NetFlow do Filebeat decodifica os fluxos e envia os eventos ao Elasticsearch. O Grafana consulta `filebeat-*`; o Kibana permite explorar o mesmo conjunto de dados.

| Arquivo | Responsabilidade |
|---|---|
| `docker-compose.yaml` | Serviços, versões, portas, rede e volumes |
| `env.example` | Modelo de configuração sem senhas preenchidas |
| `.env` | Credenciais locais; ignorado pelo Git |
| `filebeat.yml` | Módulo NetFlow e saída para Elasticsearch |
| `grafana/provisioning/datasources/elasticsearch.yaml` | Datasource Elasticsearch |
| `grafana/provisioning/dashboards/netflow.yaml` | Provisionamento do dashboard |
| `template-grafana.json` | Dashboard carregado na pasta NetFlow |
| `scripts/smoke-test.py` | Teste local de ingestão e consulta |

<a id="pre-requisitos"></a>
## ✅ Pré-requisitos

- Docker Engine com Docker Compose v2 ou superior, ou Docker Desktop com Compose.
- Python 3 para gerar o `.env` pelo exemplo e executar o teste, sem bibliotecas adicionais.
- Portas indicadas acima disponíveis e acesso aos registries para baixar as imagens.
- Como ponto de partida para laboratório: 2 vCPU e pelo menos 4 GB de RAM disponíveis para a stack. Considere 8 GB ou mais para o Docker Desktop quando houver outros projetos rodando. Isso não é um dimensionamento de produção.
- Disco conforme o volume de fluxos e a retenção. O projeto não define um prazo próprio de exclusão dos eventos.

A execução local desta atualização foi validada em Docker Desktop **ARM64**. Valide desempenho e capacidade no hardware de destino.

### Memória virtual no Linux

A documentação atual da Elastic recomenda `vm.max_map_count=1048576` para versões recentes. Consulte [configuração do sistema](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/important-system-configuration).

```bash
sudo sysctl -w vm.max_map_count=1048576
```

Para persistir, adicione `vm.max_map_count=1048576` em um arquivo de configuração de sysctl, como `/etc/sysctl.d/99-elasticsearch.conf`, e aplique com `sudo sysctl --system`.

No Docker Desktop, o kernel relevante é o da VM Linux do Docker, não o kernel do macOS. Consulte as instruções da Elastic para a sua plataforma antes de aplicar ajustes.

<a id="configuracao-env"></a>
## 🔧 Configuração e credenciais

| Variável | Uso / padrão |
|---|---|
| `TZ` | Fuso dos containers; `America/Sao_Paulo` |
| `HTTP_BIND_ADDRESS` | IP de publicação HTTP; `127.0.0.1` |
| `ES_JAVA_OPTS` | Heap da JVM; `-Xms512m -Xmx512m` |
| `ELASTIC_PASSWORD` | Senha inicial do usuário `elastic`; obrigatória |
| `KIBANA_SYSTEM_PASSWORD` | Senha do usuário interno `kibana_system`; obrigatória |
| `GRAFANA_ADMIN_USER` | Administrador inicial do Grafana; `admin` |
| `GRAFANA_ADMIN_PASSWORD` | Senha inicial do administrador; obrigatória |

O Compose recusa senhas ausentes ou vazias. O bootstrap aceita `KIBANA_SYSTEM_PASSWORD` somente com letras, números, `_` e `-`; use tokens URL-safe como os do Quick start.

O Elasticsearch tem limite de **1 GB** no Compose e heap padrão de **512 MB**. Se ampliar o heap, ajuste também o limite do container e reserve memória para os demais serviços.

### Inicialização e troca de senha

O serviço `setup_kibana_system_password` aguarda o healthcheck do Elasticsearch, configura a senha interna e encerra. O Kibana só inicia após o sucesso dessa etapa. `kibana_system` não é o usuário para login no navegador.

As variáveis de administrador do Elasticsearch e do Grafana inicializam **volumes vazios**. Alterar apenas o `.env` não troca a senha de usuários já persistidos. Para manter os dados, altere as credenciais pelas ferramentas/API de cada produto e atualize os consumidores. Recriar volumes é uma opção apenas quando a perda de todos os dados for intencional.

<a id="interfaces"></a>
## 📊 Grafana e Kibana

### Grafana

O datasource **Elasticsearch NetFlow** e o dashboard da pasta **NetFlow** são provisionados automaticamente. O UID do datasource coincide com o referenciado pelo JSON do dashboard.

Abra o [dashboard NetFlow](http://localhost:3000/d/fff4a0e1-5179-4224-b3bc-8377fc6fcdb3). Os painéis exibem **bps**, com escala decimal automática para **Kbps, Mbps e Gbps**. Cada janela fixa de 10 segundos calcula `soma(network.bytes) × 8 / 10`. Os gráficos geográficos mostram a média das janelas completas do período. Portas de origem/destino não representam, por si só, direção de entrada/saída. A atualização automática ocorre a cada **30 segundos**.

A taxa é baseada no timestamp dos eventos reportados: fluxos longos exportados em lote podem gerar picos. Ela não equivale à medição instantânea da interface nem redistribui os bytes pela duração original dos fluxos. Ajuste os timeouts de exportação conforme a resolução desejada.

A janela inicial é de **15 minutos**; ajuste o intervalo para encontrar eventos mais antigos. Sem fluxos recebidos, os painéis podem ficar sem dados.

O dashboard é mantido em `template-grafana.json`. Para preservar uma personalização, exporte o JSON e atualize esse arquivo, ou crie uma cópia com outro UID. O provisionamento não grava alterações da interface de volta no arquivo e pode substituir versões salvas na base. Veja [provisionamento do Grafana](https://grafana.com/docs/grafana/latest/administration/provisioning/).

### Kibana

Depois de receber o primeiro evento, abra **Discover** e crie uma data view com:

- Nome: `NetFlow`.
- Padrão de índice: `filebeat-*`.
- Campo de tempo: `@timestamp`.

A data view não é criada automaticamente por este Compose. Para localizar o teste, filtre `source.ip: "192.0.2.10"` e ajuste o intervalo de tempo.

<a id="exportadores-netflow"></a>
## 📡 Exportadores NetFlow

Configure o destino como **IP do host Docker** e a porta **UDP/2055**. O Filebeat suporta NetFlow v5/v9 e IPFIX, entre outros formatos descritos no [módulo oficial](https://www.elastic.co/guide/en/beats/filebeat/current/filebeat-module-netflow.html).

Para v9/IPFIX, o coletor precisa receber os templates do exportador antes de decodificar os registros. Após reiniciar o Filebeat, aguarde o reenvio dos templates. ACLs, NAT, firewall e redes do Docker Desktop devem permitir o tráfego até o coletor.

### MikroTik / RouterOS

Exemplo para NetFlow v9; ajuste interfaces e timeouts ao ambiente:

```text
/ip traffic-flow set enabled=yes interfaces=all cache-entries=4k active-flow-timeout=30m inactive-flow-timeout=15s
/ip traffic-flow target add dst-address=<IP_DO_SERVIDOR_FILEBEAT> port=2055 version=9
```

Confira os destinos existentes com `/ip traffic-flow target print` antes de adicionar outro. O timeout ativo de 30 minutos do exemplo pode atrasar a visibilidade de fluxos longos; ajuste-o se precisar de maior frequência de exportação.

Referência: [MikroTik — Traffic Flow](https://help.mikrotik.com/docs/spaces/ROS/pages/21102653/Traffic%2BFlow).

### Huawei VRP / NetStream

Exemplo de configuração NetStream para exportar **NetFlow v9** ao Filebeat em **UDP/2055**. Substitua os valores entre `<...>` antes de aplicar:

```text
system-view
ip netstream export version 9
ip netstream export host <IP_DO_SERVIDOR_FILEBEAT> 2055
ip netstream export source <IP_DE_ORIGEM_DO_EXPORTADOR>
ip netstream timeout active 1
ip netstream timeout inactive 15

interface <INTERFACE_MONITORADA>
 ip netstream inbound
 ip netstream outbound
quit
return
save
```

- `<IP_DO_SERVIDOR_FILEBEAT>`: endereço do host que executa esta stack, alcançável pelo equipamento.
- `<IP_DE_ORIGEM_DO_EXPORTADOR>`: IP local do equipamento usado como origem dos pacotes de exportação, por exemplo o endereço de uma loopback com rota até o coletor.
- `<INTERFACE_MONITORADA>`: interface cujo tráfego será coletado; repita o bloco para outras interfaces, conforme necessário.

A sintaxe, as unidades dos timeouts e a necessidade de `commit` variam conforme o modelo e a versão do VRP. Algumas plataformas usam a família de comandos `netstream export ip` em vez de `ip netstream export`. Confirme no manual do equipamento; ajuste interfaces, direção e timeouts ao seu ambiente. O comando `save` persiste a configuração após a validação.

Referência: [Huawei — exemplo de exportação de estatísticas de fluxo](https://support.huawei.cn/enterprise/en/doc/EDOC1100468733/85a6c438/example-for-configuring-flexible-flow-statistics-export).

<a id="persistencia-e-dados"></a>
## 🗃️ Persistência, retenção e atualização

Com o nome padrão do projeto Compose, os volumes são:

| Volume | Conteúdo |
|---|---|
| `nexthop_flow_stack_elasticsearch_v9_data` | Eventos, índices e estado do Elasticsearch |
| `nexthop_flow_stack_grafana_v13_data` | Banco e estado persistente do Grafana |

```bash
docker volume ls --filter name=nexthop_flow_stack
```

O Filebeat não possui volume persistente nesta configuração; seu estado local e templates em memória não sobrevivem à recriação. UDP não garante entrega, e fluxos recebidos durante interrupções podem ser perdidos.

### Retenção e backup

Não há política de retenção personalizada nesta stack. Verifique a política ILM efetiva no Elasticsearch e defina rollover/exclusão conforme a capacidade do disco. Monitore espaço livre e taxa de ingestão.

Para dados importantes, configure snapshots do Elasticsearch e backup consistente do Grafana, além de guardar as configurações e os segredos com acesso restrito. Volumes Docker não substituem backups.

### Atualização da stack antiga

Os volumes atuais têm nomes diferentes dos usados com Elastic 8.12.2/Grafana 11.2.0. Atualizar o checkout não migra nem apaga os volumes antigos automaticamente.

**Não monte um volume 8.12.2 diretamente no Elasticsearch 9.5.4.** Para preservar dados, siga o [caminho de atualização da Elastic](https://www.elastic.co/docs/deploy-manage/upgrade/deployment-or-cluster), incluindo versões intermediárias e verificação de compatibilidade. Faça backup antes da migração. Para testes do zero, use volumes novos.

Para uma atualização futura, revise as notas de versão, altere as tags no Compose, planeje a compatibilidade dos volumes e execute os testes após a inicialização. Voltar somente a tag da imagem não é um rollback seguro de dados já migrados.

<a id="operacao"></a>
## 🧰 Operação e testes

### Iniciar ou aplicar mudanças no Compose / `.env`

```bash
docker compose config -q
docker compose up -d
```

`docker compose restart` não aplica mudanças nas variáveis de ambiente do container; use `up -d` para recriá-lo quando necessário.

### Teste local de ponta a ponta

```bash
python3 scripts/smoke-test.py
```

O script verifica HTTP/saúde das aplicações, versões do Elasticsearch e Grafana, dashboard provisionado e datasource. Envia um fluxo NetFlow v5 por UDP e confirma **10 pacotes e 1.200 bytes** no Elasticsearch, seguido de consulta pela API de queries do Grafana. Sai com erro quando uma verificação falha.

O evento usa `192.0.2.10` e `198.51.100.20`, endereços reservados para documentação, e permanece no índice. O teste também consulta os nove painéis, verifica unidades em bps e confere a taxa de 960 bps para um evento de 1.200 bytes em uma janela de 10 segundos nos quatro painéis de IPs/portas. Simula o pipeline de GeoIP com IPs públicos, sem indexar esses eventos, para verificar país e organizações AS; aguarde o download inicial das bases antes de executar. Cidade/estado dependem da cobertura das bases e podem estar ausentes mesmo para IPs públicos. O teste não valida exportadores físicos, v9/IPFIX, carga sustentada, perda de pacotes ou aparência de todos os painéis.

Verificações adicionais do Filebeat:

```bash
docker compose exec -T filebeat filebeat version
docker compose exec -T filebeat filebeat test config --strict.perms=false
docker compose exec -T filebeat filebeat test output --strict.perms=false
```

### Status e logs

```bash
docker compose ps -a
docker compose logs --tail=100
docker compose logs -f filebeat
```

### Parar e retomar

```bash
docker compose stop
docker compose start
```

### Remover containers e rede, preservando volumes

```bash
docker compose down
```

### Apagar os dados desta configuração

> [!WARNING]
> **Este comando apaga os dados.** Ele remove os volumes atuais, incluindo eventos e estado do Grafana. Use somente para reinicialização intencional ou após backup.

```bash
docker compose down -v
docker compose up -d
```

Volumes antigos com nomes diferentes não são removidos por esse comando. Identifique-os antes de qualquer remoção manual. O `.env` e os arquivos montados do repositório permanecem no host.

<a id="seguranca-producao"></a>
## 🔐 Segurança em produção

- Mantenha as interfaces HTTP atrás de VPN ou proxy com TLS e autenticação; não exponha diretamente 9200/5601/3000 na Internet.
- Esta configuração usa HTTP também entre containers. Planeje TLS interno para produção.
- Filebeat e o datasource usam o superusuário `elastic` por simplicidade de laboratório. Em produção, separe identidades e permissões de ingestão, consulta e administração.
- Restrinja a origem dos pacotes UDP/2055 aos exportadores autorizados.
- Mantenha `.env` fora do Git, use senhas exclusivas e proteja backups/segredos.
- Configure chaves persistentes de criptografia do Kibana para sessões, saved objects e reporting. O Compose atual não define essas chaves; alguns recursos de alertas/actions ficam indisponíveis e sessões podem ser invalidadas em reinícios.
- O downloader GeoIP do Elasticsearch está ativado e baixa as bases City/Country/ASN. Requer acesso à Internet aos endpoints da Elastic e de armazenamento das bases. IPs privados/reservados podem não ter localização ou organização AS; eventos antigos não são enriquecidos retroativamente.

<a id="troubleshooting"></a>
## 🧯 Troubleshooting

### Compose acusa senha ausente

Preencha as três senhas do `.env` ou gere o arquivo pelo Quick start. `env.example` propositalmente não fornece credenciais prontas.

### Porta já está em uso

Identifique o processo/container que ocupa a porta. Ajustar as portas publicadas exige atualizar também URLs e o teste local; não encerre serviços de outros projetos sem verificar sua finalidade.

### Elasticsearch reinicia ou não inicia

Confira `docker compose logs --tail=100 elasticsearch`, memória disponível, espaço em disco, `vm.max_map_count` e compatibilidade do volume com a versão. Aumentar só o heap sem ajustar o limite de 1 GB pode causar falta de memória.

### Elasticsearch retorna 401 ou aparece healthy sem aceitar login

O healthcheck do Compose aceita 200/401 para detectar que o endpoint está respondendo. Isso não comprova credenciais válidas nem saúde do cluster. O smoke test faz a verificação autenticada e aceita cluster `green` ou `yellow`; em single-node, réplicas não alocadas podem causar `yellow`.

### Kibana não conecta

```bash
docker compose logs --tail=100 setup_kibana_system_password kibana
```

O setup deve encerrar com código 0. Confirme credenciais, formato URL-safe de `KIBANA_SYSTEM_PASSWORD` e se houve alteração de senha no `.env` sem atualização do usuário persistido.

### Grafana sem dados ou datasource com erro

Confira autenticação do datasource, existência de eventos em `filebeat-*` e intervalo de tempo. Antes do primeiro evento, o índice pode ainda não existir. Execute o smoke test e consulte os logs do Filebeat. Para personalizações do dashboard, mantenha o UID do datasource coerente com o JSON.

### Fluxos do equipamento não aparecem

Verifique destino/porta, interface de origem, ACLs e chegada dos pacotes UDP ao host. Em v9/IPFIX, aguarde os templates. Confira os timeouts de exportação, horário do equipamento e logs do Filebeat. O sucesso do teste local comprova ingestão local, mas não a conectividade entre roteador e host.

### `filebeat test output` avisa que TLS está desativado

É esperado no laboratório: a saída está configurada como `http://elasticsearch:9200`. Para produção, configure TLS e a confiança nos certificados.

<a id="materiais"></a>
## 📚 Materiais

- [Template do dashboard Grafana](./template-grafana.json).
- [Apresentação na GTER](./%5BGTER%2054%5D%20Elizandro%20Pacheco.pdf).

<a id="apoiadores"></a>
## 🤝 Apoiadores

Obrigado aos apoiadores que fortalecem a iniciativa e a comunidade:

### NextHop Solutions®

<a href="https://nexthop.solutions/">
  <img
    src="https://nexthop.solutions/assets/logo-horizontal.png"
    alt="NextHop Solutions®"
    width="260"
  />
</a>

- 🌐 Site: [nexthop.solutions](https://nexthop.solutions/)

### EvoCODE IA®

<a href="https://evocode.ia.br/">
  <img
    src="https://evocode.ia.br/logo-evocode.png"
    alt="EvoCODE IA®"
    width="260"
  />
</a>

- 🌐 Site: [evocode.ia.br](https://evocode.ia.br/)

---

<a id="contato"></a>
## 📫 Contato

- **Desenvolvedor**: Elizandro Pacheco
- **Instagram**: [`@elizandropacheco`](https://instagram.com/elizandropacheco)
- **WhatsApp**: [`+55 51 99871-8111`](https://wa.me/5551998718111)

<a id="licenca"></a>
## 📄 Licença

Este projeto é distribuído sob a licença **Apache 2.0**. Veja o arquivo `LICENSE`.

NextHop Solutions®, EvoCODE IA® e Network Education® são marcas registradas. A licença do código não concede direitos sobre essas marcas.

As imagens e dependências utilizadas possuem suas próprias licenças; a licença do repositório não substitui as condições de cada componente.

A tradução de referência está em [LICENSE.pt-BR.md](./LICENSE.pt-BR.md). O texto aplicável do projeto está em [LICENSE](./LICENSE).

### Resumo simples (o que pode e o que não pode) 🔎

> Nota: este é um resumo prático e **não** substitui a leitura do `LICENSE` (nem é aconselhamento jurídico).

#### Você PODE ✅

- **Usar** a stack/código para qualquer finalidade (inclusive **comercial**).
- **Modificar** (criar derivações/forks), inclusive “rebatizar” o seu fork e manter outro mantenedor.
- **Redistribuir** (publicar) o original ou versões modificadas (em código-fonte ou empacotado).

#### Você DEVE 📌

- **Incluir uma cópia da licença Apache 2.0** quando redistribuir.
- **Manter avisos de copyright/atribuição** e notices existentes.
- **Indicar mudanças**: arquivos modificados devem conter aviso claro de que foram alterados.
- Se houver arquivo `NOTICE` no futuro, **reproduzir o conteúdo aplicável** ao redistribuir.

#### Você NÃO PODE 🚫

- **Usar marcas/nome/logotipos** da NextHop Solutions® (ou de terceiros) como se houvesse endosso/afiliações: a Apache 2.0 **não concede licença de marca** (ver “Trademarks” no `LICENSE`).
- **Remover atribuições/avisos legais** existentes do projeto original ao redistribuir.

Em outras palavras: **sim**, a Apache 2.0 permite você usar/alterar/redistribuir e até trocar o mantenedor do *seu fork*, **desde que** você cumpra as obrigações de atribuição/licença e não use marcas como se fossem permissão/endorso.

### Licença em PT-BR (referência) 🇧🇷

Para facilitar leitura, existe também o arquivo `LICENSE.pt-BR.md` (referência). Em caso de dúvida legal, use sempre o `LICENSE` (EN).
