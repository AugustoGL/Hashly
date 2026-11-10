FROM node:22-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# La URL del API se incrusta en el build del cliente
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build


FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production

COPY --from=build /app ./

USER node
EXPOSE 3000
CMD ["npm", "start"]
