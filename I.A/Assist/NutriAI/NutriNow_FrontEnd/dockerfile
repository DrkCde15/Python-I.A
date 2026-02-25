# 1. Imagem para build do Angular
FROM node:20-alpine AS build

WORKDIR /app

# Copia package.json e package-lock.json para instalar dependências
COPY package*.json ./

RUN npm ci

# Copia todo o código do projeto
COPY . .

# Faz o build do Angular em modo produção
RUN npm run build -- --output-path=dist --configuration production

# 2. Imagem final com Nginx para servir os arquivos estáticos
FROM nginx:alpine

# Copia os arquivos construídos do build
COPY --from=build /app/dist /usr/share/nginx/html

# Copia configuração customizada do Nginx (opcional)
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expõe a porta padrão do Nginx
EXPOSE 80

# Comando padrão ao iniciar o container
CMD ["nginx", "-g", "daemon off;"]
