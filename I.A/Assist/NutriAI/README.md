# 🥗 NutriAI – Seu Nutricionista Virtual com IA

*Planos alimentares, treinos e nutrição personalizada em um só lugar!*

---

## 📖 Sobre o Projeto

O **NutriAI** é um assistente virtual desenvolvido em **Python** com integração à **IA Generativa (Google Gemini)**, especializado em **nutrição esportiva, dietas personalizadas e treinos físicos**.

Ele cria **planos alimentares detalhados**, sugere **treinos alinhados aos objetivos do usuário**, fornece **tabelas nutricionais estimadas** para entregar recomendações cada vez mais precisas. Tudo isso com uma linguagem clara, objetiva e motivadora.

---

## 🚀 Funcionalidades

✅ **Planos Alimentares Personalizados** – Baseados no objetivo, restrições e preferências do usuário.  
✅ **Sugestões de Refeições Detalhadas** – Incluindo calorias, carboidratos, proteínas e gorduras.  
✅ **Treinos Alinhados ao Objetivo** – Academia ou treino em casa, conforme meta do usuário.  
✅ **Histórico de Conversas** – Mantém contexto e melhora recomendações ao longo da sessão.  
✅ **Respostas Claras e Objetivas** – Sem enrolação, evitando jargão técnico excessivo.  
✅ **Verificação de Informações** – Solicita dados adicionais se necessário, não inventa informações.

---

## 📦 Tecnologias Utilizadas

* **Python**
* **Google Gemini API** (IA generativa)
* **Flask** (Backend)
* **Flask_cors** (Conecção com o frontend)
* **LangChain** (Memória de conversas e orquestração do agente)
* **mysql.connector** (Banco de dados MySQL para histórico de chat)
* **dotenv** (Variáveis de ambiente)
* **FoodAnalyser** (Ferramenta customizada de análise nutricional)

---

## ⚙️ Como Usar

### 1️⃣ Pré-requisitos

* Python 3.10 ou superior instalado
* Chave da API Google Gemini no arquivo `.env`
* Instalar dependências: pip install -r requirements.txt

### 2️⃣ Executando o NutriAI

`python api.py`

Digite suas perguntas ou objetivos (ex: “Quero ganhar massa muscular”) e receba planos e treinos detalhados.
---

## 📁 Estrutura do Projeto

```
NutriAI/
├── .env                # Variáveis de ambiente (API keys)
├── api.py          # Script para o funcionamento da I.A no backend
├── food_analyser.py    # Ferramenta para análise de imagens
├── nutri.py          # Script principal do agente nutricionista
├── chat_history.db     # Banco SQLite para histórico de chat
└── requirements.txt    # Dependências do projeto
```

---

## 👤 Desenvolvedor

**Júlio Cesar**

* Desenvolvedor e entusiasta de IA, automação.
* Contato: [jcesarsantana215@gmail.com](mailto:jcesarsantana215@gmail.com)
* LinkedIn: [https://www.linkedin.com/in/julio-santana-ads/](https://www.linkedin.com/in/julio-santana-ads/)
