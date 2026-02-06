# ---- Stage 1: The Builder ----
FROM node:20-alpine AS builder
WORKDIR /app

# Declare build arguments
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_GOOGLE_SHEET_WEBHOOK_URL

# Set them as environment variables for the 'npm run build' command
ENV NEXT_PUBLIC_SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL}
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_ANON_KEY}
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_GOOGLE_SHEET_WEBHOOK_URL=${NEXT_PUBLIC_GOOGLE_SHEET_WEBHOOK_URL}

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

# Create a non-root user for security
RUN addgroup -S nodejs && adduser -S nextjs -G nodejs -u 1001

# Runtime environment variables (set before USER command)
ARG API_URL_INTERNAL
ARG NEXT_PUBLIC_API_URL
ENV API_URL_INTERNAL=${API_URL_INTERNAL}
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NODE_ENV=production

# Copy the standalone output structure
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose the port Next.js runs on
EXPOSE 3000

# Start the production Next.js server
CMD ["node", "server.js"]