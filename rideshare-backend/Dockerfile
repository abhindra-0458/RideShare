FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN addgroup -g 1001 -S nodejs
RUN adduser -S rideshare -u 1001
RUN mkdir -p uploads logs && chown -R rideshare:nodejs uploads logs

USER rideshare

EXPOSE 3000

CMD ["npm", "start"]
