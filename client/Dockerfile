# Stage 1: Build the Next.js app
FROM node:16-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --only=production  # Install only production dependencies

COPY . ./
RUN npm run build  # Build Next.js app

# Stage 2: Serve the built app
FROM node:16-alpine AS runner
WORKDIR /app
ENV NODE_ENV production

# Copy built app files only (exclude node_modules)
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./

# Install only necessary production dependencies in final stage
RUN npm install --only=production

# Expose port 3000
EXPOSE 3000
CMD ["npm", "run", "start"]