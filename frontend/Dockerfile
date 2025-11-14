# ---- Stage 1: The Builder ----
FROM node:20-alpine AS builder
WORKDIR /app

# Declare build arguments
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_API_URL

# Set them as environment variables for the 'npm run build' command
ENV NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL}
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY}
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Copy package.json and lock file
COPY package*.json ./
RUN npm ci

# Copy the rest of your source code
COPY . .

# Run the build
RUN npm run build

# ---- Stage 2: The Production Server ----
    
FROM node:20-alpine
WORKDIR /app

# Create a non-root user for security (Keep this!)
RUN addgroup -S nodejs && adduser -S nextjs -G nodejs -u 1001
USER nextjs

# Fix 1: Add internal API variable declarations for runtime access (Keep this!)
ARG API_URL_INTERNAL
ARG NEXT_PUBLIC_API_URL
ENV API_URL_INTERNAL=${API_URL_INTERNAL}
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# -------------------------------------------------------------
# CRITICAL FIX: Use the Standalone Output Structure
# -------------------------------------------------------------

# 1. Copy the core application files (server.js, node_modules, etc.) directly to /app
# This puts server.js at /app/server.js
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone /app

# 2. Copy the static assets to /app/public
COPY --from=builder --chown=nextjs:nodejs /app/public /app/public

# -------------------------------------------------------------

# Expose the port Next.js runs on
EXPOSE 3000

# Fix 2: Start the production Next.js server (This line is now correct)
CMD ["node", "server.js"]