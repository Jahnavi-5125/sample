# Multi-stage build for Next.js production
# 1) Builder: install deps and build
FROM node:18-alpine AS builder
WORKDIR /app

# Install dependencies based on lockfile if present
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./
RUN if [ -f package-lock.json ]; then npm ci; \
    elif [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    elif [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i --frozen-lockfile; \
    else npm install; fi

# Copy source
COPY . .

# Build for production
ENV NODE_ENV=production
RUN npm run build

# 2) Runner: minimal image to run `next start`
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

# Copy only what is needed to run the app
COPY --from=builder /app/package.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.* ./

EXPOSE 3000

CMD ["npm", "run", "start"]
