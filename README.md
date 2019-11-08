# ProductStars API

Documentação destinada à descrever a estrutura da API e sua utilização

## Configuração

- O arquivo requirements.txt lista todas as dependências necessárias ao projeto

- No arquivo config.py são encontradas as chaves que precisam ser configuradas em um arquivo .env na raiz do projeto, de onde virão informações como acesso a banco de dados, tipo de cache, tamanho de paginação e informações para autenticação, como uma secret key e uma senha

## Login

É necessário se autenticar para receber um token e utilizar as chamadas da API. Para isso, faça uma requisição HTTP get para a rota /login e armazene o token retornado. Ele será utilizado como parâmetro de query string nas chamadas.

## Pessoas

##### Endpoints :
- GET /person?token={{token}}
 
    retorna lista de pessoas cadastradas
    
- POST /person/?token={{token}}

    {{token}} = token obtido no login
    
    Payload: { 'name': name, 'email': email}
    
    Insere um usuário no banco de dados, validando se o e-mail já existe
    
- PUT /person/{{person_id}}?token={{token}}

    {{token}} = token obtido no login
    
    {{person_id}} = Guid do person
    
    Payload: { 'name': name, 'email': email }
    
    Atualiza informações de uma pessoa
    
- DELETE /person/{{person_id}}?token={{token}}
    
    {{token}} = token obtido no login
    
    {{person_id}} = Guid do person
    
    Remove uma pessoa do banco de dados


## Produtos

##### Endpoints :

- GET /person/{{person_id}}/product?token={{token}}&page={{page}}

    {{token}} = token obtido no login
    
    {{person_id}} = Guid do person
    
    {{page}} = Número da página
    
    Baseado na configuração de paginação, a API divide o total de registros pelo threshold configurado e dá o número de páginas, não permitindo acessar uma página não existente
    
- POST /person/{{person_id}}/product?token={{token}}

    {{token}} = token obtido no login
    
    {{person_id}} = Guid do person
    
    Payload: { 'product_id': product_id }
    
    Product ID a ser inserido em uma lista de uma pessoa. Caso o produto não exista ou já esteja na lista da pessoa, erros customizados são retornados. A lista de produtos é obtida via API externa configurada no arquivo de configuração: http://challenge-api.luizalabs.com/api/product/?page={{page}} 

## Cache

As chamadas de listagem e de maior processamento possuem cache de 1 hora. Contudo, há um endpoint que limpa cache por chave ou limpa todo o cache.

##### Endpoints :

- POST /cache/clear?token={{token}}

    {{token}} = token obtido no login
    
    Payload: { 'cache_key': cache_key }
    
    cache_key - chave a ser limpada no cache, ou "all" para limpeza geral
    
## Tests

Dentro da pasta /tests há um arquivo com alguns testes básicos. Para rodar, basta instalar o pacote pytest que está informado no arquivo de requirements (```pip install pytest```) e rodar o comando ```pytest -v``` na raiz do projeto.

## Ping

Todos os endpoints (```/login```, ```/person```, ```/cache```) possuem uma rota ```/ping``` que não exige autenticação para validação de status da API.