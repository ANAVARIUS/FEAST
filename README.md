# F.E.A.S.T. (Frictionless Engagement & Agentic Service Technology)

F.E.A.S.T. es un ecosistema de agentes inteligentes orquestados para la gestión integral de pedidos en restaurantes. A diferencia de las aplicaciones de delivery tradicionales, la interacción se realiza enteramente a través de **Telegram**, permitiendo una comunicación fluida y natural mediante lenguaje procesado por IA.

El sistema opera bajo un modelo **B2B2C**, donde cada restaurante afiliado dispone de agentes entrenados específicamente con su menú y reglas de negocio.

## Stack Tecnológico

* **Lenguaje:** Python
* **Orquestación de Agentes:** LangGraph
* **Infraestructura:** Docker & Docker Compose
* **Cloud (AWS):** RDS, Bedrock, OpenSearch Serverless
* **Migraciones:** Alembic
* **Pagos:** Stripe
* **Gestión de Tareas:** Trello API

## Arquitectura

El proyecto emplea una **Arquitectura Orientada a Servicios (SOA)** centrada en agentes. Utiliza un flujo de control basado en grafos para gestionar el estado de la conversación, permitiendo que múltiples agentes especializados colaboren en la toma de pedidos, consultas de inventario y transacciones financieras.

## Requisitos Previos

Para desplegar el proyecto, es necesario contar con:

1.  **Entorno de Ejecución:**
    * Docker y Docker Compose.
    * Sistema operativo compatible con **POSIX** (Linux/macOS) para la ejecución de scripts.
    * Utilidad **Make**.
2.  **Infraestructura Cloud (AWS):**
    * Un rol de AWS con permisos de acceso a: `RDS`, `Bedrock` y `OpenSearch Serverless`.
3.  **Cuentas y APIs:**
    * Bot de Telegram registrado (Token de BotFather).
    * Tablero de Trello con una lista configurada para pedidos.
    * Cuenta activa en Stripe para el procesamiento de pagos.

## Instalación y Despliegue

Siga estos pasos para inicializar el sistema:

1.  **Clonar el repositorio:**
    ```bash
    git clone <url-del-repositorio>
    cd FEAST
    ```

2.  **Variables de Entorno:**
    Cree un archivo `.env` basado en el ejemplo proporcionado y complete la información requerida:
    ```bash
    cp .env.example .env
    ```

3.  **Levantamiento del Sistema:**
    Utilice el `Makefile` para automatizar la construcción y el despliegue de los servicios:
    ```bash
    make all
    ```

## Uso

Una vez desplegado:
* Envíe un mensaje a la cuenta de Telegram del bot configurado.
* Interactúe de forma natural para realizar pedidos o consultar información.

## Mantenimiento

Para detener los servicios y limpiar el entorno de ejecución:
```bash
make clean