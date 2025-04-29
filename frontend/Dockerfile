# Use official Node image
FROM node:latest

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173 
CMD ["npm", "run", "dev", "--", "--host"]
