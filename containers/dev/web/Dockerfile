FROM node:22-alpine

VOLUME /app

WORKDIR /app

COPY dungeon-times-web/package.json .

RUN npm install

CMD [ "npx",  "vite" ]