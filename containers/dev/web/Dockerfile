FROM node:22-alpine

VOLUME /app

WORKDIR /app

COPY dungeon-times-web/package.json .

COPY dungeon-times-web/package-lock.json .

RUN npm install

CMD [ "npx",  "vite" ]