# syntax=docker/dockerfile:1

# Base image used for all stages
FROM node:20-alpine AS base
ENV NODE_ENV=production
WORKDIR /app

# Some Next.js dependencies expect this for better compatibility
RUN apk add --no-cache libc6-compat

# ----------------------------
# Development image
# ----------------------------
FROM base AS dev
ENV NODE_ENV=development
WORKDIR /app
COPY package*.json ./
# Install dev dependencies (node_modules will be mounted via a named volume in compose)
RUN npm install
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ----------------------------
# Build image
# ----------------------------
FROM base AS build
ENV NODE_ENV=production
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ----------------------------
# Production runtime image
# ----------------------------
FROM node:20-alpine AS prod
ENV NODE_ENV=production
WORKDIR /app
RUN apk add --no-cache libc6-compat
# Copy only what we need to run `next start` in production
COPY --from=build /app/package*.json ./
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/node_modules ./node_modules
EXPOSE 3000
CMD ["npm", "run", "start"]