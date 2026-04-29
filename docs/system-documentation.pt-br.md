# Documentação do Sistema Perazzo API

Este documento explica como o backend funciona, como os principais fluxos de negócio foram implementados e quais arquivos são responsáveis por cada etapa. Todas as rotas da API são montadas com o prefixo `/api/v1` por `app/main.py` e `app/api/v1/routes.py`.

## Visão Geral da Arquitetura

O backend é uma aplicação FastAPI organizada em routers, services, schemas e models SQLAlchemy.

- `app/main.py` cria a aplicação FastAPI, configura CORS, registra o router v1 e expõe `/health`.
- `app/api/v1/routes.py` registra todos os routers de módulos.
- `app/api/v1/routers/*.py` define endpoints HTTP e contratos de entrada/saída.
- `app/services/*.py` contém regras de negócio, persistência, validações e serialização.
- `app/domain/models/*.py` define os models SQLAlchemy do banco.
- `app/schemas/*.py` define payloads e respostas Pydantic.
- `app/core/config.py` carrega variáveis de ambiente com `pydantic-settings`.
- `app/core/database.py` cria engine SQLAlchemy e sessões por request.
- `app/core/dependencies.py` resolve o usuário autenticado a partir do bearer token.
- `migrations/` contém as migrations Alembic.

O backend é isolado por loja. A maioria das entidades autenticadas pertence a um `store_id`, e os services resolvem essa loja com `StoreService.get_by_user_id(current_user.id)`.

## Fluxo de Autenticação e Criação de Conta

A criação de conta começa em `POST /api/v1/auth/register`, implementado em `app/api/v1/routers/auth.py`. O router recebe `UserCreate`, chama `UserService.create()` em `app/services/user.py`, cria o hash da senha via `app/core/security.py`, salva o usuário, gera um token de verificação de email com `create_email_verification_token()` em `app/util/jwt.py`, salva apenas o hash HMAC desse token com `app/util/token_hash.py` e envia o link por `send_email_verification_email()` em `app/services/email.py`. O token bruto de verificação nunca é retornado pela API.

O login usa `POST /api/v1/auth/login`. O router chama `UserService.authenticate()`, que busca o usuário por email e valida a senha. Se estiver correto, o router retorna um bearer token criado por `create_access_token()`. O payload do token guarda o id do usuário em `sub`.

Endpoints protegidos dependem de `get_current_user()` em `app/core/dependencies.py`. Essa dependência lê o header `Authorization: Bearer <token>`, decodifica o token com `decode_access_token()`, valida o UUID em `sub` e carrega o usuário com `UserService.get_by_id()`.

A verificação de email é feita por `POST /api/v1/auth/email/verify`. O endpoint decodifica o token de email, carrega o usuário, valida o token contra o hash salvo, marca `is_email_verified=True` e limpa `email_verification_token`.

A recuperação de senha usa `POST /api/v1/auth/password/forgot` para gerar um `reset_password_token`, salvar apenas o hash HMAC desse token no usuário e enviar o email de redefinição de senha. O endpoint fica em `app/api/v1/routers/auth.py`; ele chama `create_password_reset_token()` de `app/util/jwt.py` e `send_password_reset_email()` de `app/services/email.py`. A API nunca retorna o token para o cliente. Ela retorna uma mensagem genérica para impedir que alguém descubra se um email está cadastrado.

Os links de redefinição são montados a partir de `FRONTEND_URL` e apontam para `/reset-password?token=<token>`. As configurações SMTP são carregadas em `app/core/config.py` pelas variáveis `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME` e `SMTP_USE_TLS`. Em desenvolvimento local, se SMTP não estiver configurado, `app/services/email.py` escreve o link de reset no log da API em vez de retorná-lo na resposta HTTP. Em produção, o SMTP deve ser configurado pelas variáveis de ambiente do Render, por exemplo usando Resend.

Em produção, `FRONTEND_URL` e `BACKEND_CORS_ORIGINS` devem incluir `https://perazzo-manager.vercel.app`.

`POST /api/v1/auth/password/reset` recebe o token e a nova senha, decodifica o token com `decode_password_reset_token()`, valida se ele corresponde ao último hash salvo, valida as regras da senha com `validate_password_rules()`, substitui o hash da senha com `hash_password()`, limpa `reset_password_token` e salva a alteração. Login e recuperação de senha também usam limites simples de requisição em `app/core/rate_limit.py`.

A atualização do perfil usa `PUT /api/v1/auth/me`, exige autenticação e delega para `UserService.update()`.

## Fluxo de Loja

Os endpoints autenticados de loja ficam em `app/api/v1/routers/store.py`.

- `POST /api/v1/store` cria a loja do usuário atual.
- `GET /api/v1/store/me` retorna a loja do usuário atual.
- `PATCH /api/v1/store/me` atualiza configurações da loja.
- `PATCH /api/v1/store/me/today-open` altera o estado aberto/fechado do dia atual.
- `GET /api/v1/store/{slug}` retorna uma loja pelo slug.

As regras de negócio ficam em `app/services/store.py`. Um usuário só pode ter uma loja. Slugs são gerados por `app/util/slug.py`. Horários de funcionamento são normalizados e validados por `app/util/store_hours.py`. A serialização da loja também calcula `is_open_now`, usado pelo catálogo para decidir se clientes podem adicionar itens ao carrinho ou finalizar pedido.

## Fluxo de Produtos e Categorias

Produtos são implementados por `app/api/v1/routers/product.py` e `app/services/product.py`.

- `POST /api/v1/products` cria produto.
- `GET /api/v1/products` lista produtos com paginação, busca, filtro de categoria, ordenação e `X-Total-Count`.
- `GET /api/v1/products/{slug}` retorna produto por slug.
- `PATCH /api/v1/products/{product_id}` atualiza produto.
- `DELETE /api/v1/products/{product_id}` desativa o produto e remove o item de carrinhos.

Produtos são escopados pela loja do usuário atual. Slugs de produto são únicos por loja. Se o estoque for `0`, o produto é automaticamente marcado como inativo. Consultas de catálogo retornam apenas produtos ativos e, em modo catálogo, produtos com estoque disponível ou estoque ilimitado.

Categorias são implementadas por `app/api/v1/routers/category.py` e `app/services/category.py`.

- `POST /api/v1/categories` cria categoria.
- `GET /api/v1/categories` lista categorias por `sort_order` e nome.
- `GET /api/v1/categories/{slug}` retorna categoria.
- `PATCH /api/v1/categories/{category_id}` atualiza categoria.
- `POST /api/v1/categories/reorder` salva ordenação manual.
- `DELETE /api/v1/categories/{category_id}` remove categoria.

Categorias são escopadas por loja. Novas categorias recebem o próximo `sort_order`. A relação produto-categoria é definida em `app/domain/models/product_category.py`.

## Fluxo do Catálogo Público

Endpoints do catálogo público são implementados em `app/api/v1/routers/catalog.py`. Eles não exigem autenticação, mas só funcionam para lojas com `has_catalog_active` igual a true.

- `GET /api/v1/catalog/{store_slug}/home` retorna loja, categorias e seções da home.
- `GET /api/v1/catalog/{store_slug}/products` lista produtos públicos.
- `GET /api/v1/catalog/{store_slug}/categories/{category_slug}` lista produtos de uma categoria.
- `GET /api/v1/catalog/{store_slug}/products/{product_slug}` retorna a página pública de um produto.
- `GET /api/v1/catalog/{store_slug}/payment-methods` lista formas de pagamento para checkout.
- `GET /api/v1/catalog/{store_slug}/delivery-methods` lista formas de entrega para checkout.

O router de catálogo usa `StoreService`, `CategoryService`, `ProductService`, `PaymentMethodService` e `DeliveryMethodService`. Ele serializa um formato público menor por helpers no próprio `catalog.py`. Endpoints que alteram carrinho ou finalizam pedido chamam `_ensure_store_open_for_cart_actions()`, bloqueando ações quando a loja está fechada.

## Fluxo de Carrinho

Existem duas superfícies de carrinho: carrinhos autenticados do dashboard e carrinhos públicos do catálogo. Ambas usam `CartService` em `app/services/cart.py`.

Endpoints autenticados de carrinho ficam em `app/api/v1/routers/cart.py`:

- `POST /api/v1/carts` cria carrinho com o primeiro produto.
- `GET /api/v1/carts` lista carrinhos.
- `GET /api/v1/carts/{cart_id}` retorna carrinho.
- `PATCH /api/v1/carts/{cart_id}` atualiza dados do cliente, entrega, pagamento ou adiciona produtos.
- `PUT /api/v1/carts/{cart_id}/products` substitui a lista de produtos.
- `POST /api/v1/carts/{cart_id}/checkout` transforma carrinho em pedido.
- `DELETE /api/v1/carts/{cart_id}` remove carrinho.

Endpoints públicos de carrinho ficam em `app/api/v1/routers/catalog.py`:

- `POST /api/v1/catalog/{store_slug}/carts`
- `GET /api/v1/catalog/{store_slug}/carts/{cart_id}`
- `PUT /api/v1/catalog/{store_slug}/carts/{cart_id}/products`
- `POST /api/v1/catalog/{store_slug}/carts/{cart_id}/preview-total`
- `POST /api/v1/catalog/{store_slug}/carts/{cart_id}/checkout`
- `DELETE /api/v1/catalog/{store_slug}/carts/{cart_id}`

Endpoints públicos de carrinho exigem `cart_id` e `cart_secret`. `CartService.create()` gera `cart_secret` com `secrets.token_urlsafe()`. A API retorna esse segredo quando o carrinho é criado, e leituras, atualizações, preview de total, checkout e remoção exigem `cart_secret` como query parameter. Assim, o UUID do carrinho sozinho não funciona como autorização completa.

`CartService.create()` valida se o produto existe, pertence à loja, está ativo e tem estoque suficiente. `replace_products()` apaga o carrinho quando a lista de produtos fica vazia. `checkout()` exige produtos, nome do cliente, telefone do cliente e forma de pagamento. O checkout público ainda valida método de entrega e endereço quando entrega é selecionada, resolve a forma de pagamento por id, cria um payload `OrderCreate`, delega para `OrderService.create()` e apaga o carrinho.

## Fluxo de Pedidos

Pedidos são implementados por `app/api/v1/routers/order.py` e `app/services/order.py`.

- `POST /api/v1/orders` cria pedido.
- `GET /api/v1/orders` lista pedidos por data, com paginação e busca opcional.
- `GET /api/v1/orders/search` busca por número do pedido, nome do cliente, telefone do cliente ou produto.
- `GET /api/v1/orders/{order_id}` retorna um pedido.
- `PATCH /api/v1/orders/{order_id}` atualiza produtos, cliente, entrega, entregador e pagamento.
- `DELETE /api/v1/orders/{order_id}` remove pedido.
- `PUT /api/v1/orders/{order_id}/status` altera status.
- `POST /api/v1/orders/preview-total` calcula total antes de salvar.

`OrderService.create()` resolve a loja, carrega produtos ativos, gera um número curto de pedido, busca ou cria cliente por telefone, resolve método de entrega, associa entregador opcionalmente, calcula totais dos itens e da entrega, e salva o pedido com status `pending`.

Mudanças de status controlam estoque e métricas de cliente. Em `OrderService.update_status()`, mudar para `confirmed` ou `deliveried` reduz estoque uma única vez. Mudar para `canceled` restaura estoque se ele tinha sido reduzido. Entrar em `deliveried` incrementa contadores de pedidos entregues e total gasto do cliente; sair de `deliveried` decrementa essas métricas.

A listagem de pedidos usa por padrão a data atual no timezone `America/Sao_Paulo`. A serialização inclui produtos, métricas do cliente, método de entrega, entregador, status, forma de pagamento, observação, total e timestamps.

## Clientes

Clientes são implementados por `app/api/v1/routers/customer.py` e `app/services/customer.py`.

- `POST /api/v1/customers`
- `GET /api/v1/customers`
- `GET /api/v1/customers/{customer_id}`
- `PATCH /api/v1/customers/{customer_id}`
- `DELETE /api/v1/customers/{customer_id}`

Clientes são escopados por loja. A listagem retorna `orders_count` por subquery. A exclusão é cuidadosa: pedidos são reassociados a um cliente fallback de "cliente removido" para não perder histórico.

## Formas de Pagamento e Entrega

Formas de pagamento são implementadas por `app/api/v1/routers/payment_method.py` e `app/services/payment_method.py`.

- `POST /api/v1/payment-methods`
- `GET /api/v1/payment-methods`
- `GET /api/v1/payment-methods/{payment_method_id}`
- `PATCH /api/v1/payment-methods/{payment_method_id}`
- `DELETE /api/v1/payment-methods/{payment_method_id}`

Nomes de formas de pagamento devem ser únicos por loja.

Formas de entrega são implementadas por `app/api/v1/routers/delivery_method.py` e `app/services/delivery_method.py`.

- `POST /api/v1/delivery-methods`
- `GET /api/v1/delivery-methods`
- `GET /api/v1/delivery-methods/{delivery_method_id}`
- `PATCH /api/v1/delivery-methods/{delivery_method_id}`
- `DELETE /api/v1/delivery-methods/{delivery_method_id}`

Formas de entrega representam bairros ou áreas de entrega com preço. Elas são obrigatórias para pedidos de entrega e entram no cálculo do total.

## Caixa

O caixa é implementado por `app/api/v1/routers/cash_register.py` e `app/services/cash_register.py`.

- `GET /api/v1/cash-register/summary`
- `POST /api/v1/cash-register/entries`
- `PATCH /api/v1/cash-register/entries/{entry_id}`
- `DELETE /api/v1/cash-register/entries/{entry_id}`

O resumo combina receita automática de pedidos com entradas manuais, despesas manuais e retiradas de lucro. `CashRegisterService.get_summary()` suporta visões por dia, semana, mês e ano. Ele agrupa valores por forma de pagamento e calcula totais como entradas automáticas, entradas manuais, despesas, retiradas de lucro, total de entrega e saldo.

## Entregadores

Entregadores são implementados por `app/api/v1/routers/courier.py` e `app/services/courier.py`.

- `POST /api/v1/couriers`
- `GET /api/v1/couriers`
- `PATCH /api/v1/couriers/{courier_id}`
- `DELETE /api/v1/couriers/{courier_id}`
- `POST /api/v1/couriers/adjustments`
- `PATCH /api/v1/couriers/adjustments/{adjustment_id}`
- `DELETE /api/v1/couriers/adjustments/{adjustment_id}`
- `GET /api/v1/couriers/summary`

Entregadores podem ser associados a pedidos de entrega. O resumo calcula quantidade de entregas, valor de entrega, ajustes manuais, entregas sem entregador e total a receber por entregador em períodos de dia, semana, mês ou ano.

## Regras de Propriedade dos Dados

A principal regra de segurança é o isolamento por loja. Services resolvem `store_id` a partir do usuário autenticado ou recebem um `store_id` explícito nos fluxos públicos do catálogo. Consultas de produtos, categorias, clientes, pedidos, carrinhos, formas de pagamento, formas de entrega, entregadores e caixa sempre filtram por loja.

Routers autenticados usam `dependencies=[Depends(get_current_user)]`, enquanto rotas públicas de catálogo validam a loja por slug e checam se o catálogo está ativo.
