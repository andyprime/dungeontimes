FROM node:22-alpine

VOLUME /app

WORKDIR /app

COPY web/package.json .

COPY web/package-lock.json .

RUN npm install

CMD [ "npx",  "vite" ]