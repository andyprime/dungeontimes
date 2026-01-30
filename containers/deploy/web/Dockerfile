FROM node:22-alpine AS build

WORKDIR /app

COPY web/package.json web/package-lock.json .

RUN npm ci

COPY /web .

# RUN vite build
RUN npm run build


FROM nginx:alpine

RUN adduser -D -H -u 1001 -s /sbin/nologin webuser

RUN mkdir -p /app/www

COPY --from=build /app/dist /app/www

COPY containers/deploy/web/nginx.conf /etc/nginx/templates/default.conf.template

RUN chown -R webuser:webuser /app/www && \
    chmod -R 755 /app/www && \
    # Nginx needs to read and write to these directories
    chown -R webuser:webuser /var/cache/nginx && \
    chown -R webuser:webuser /var/log/nginx && \
    chown -R webuser:webuser /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R webuser:webuser /var/run/nginx.pid && \
    chmod -R 777 /etc/nginx/conf.d

EXPOSE 80

ENV NGINX_ENVSUBST_TEMPLATE_DIR=/etc/nginx/templates
ENV NGINX_ENVSUBST_TEMPLATE_SUFFIX=.template
ENV NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx/conf.d
ENV PORT=80

CMD ["nginx", "-g", "daemon off;"]