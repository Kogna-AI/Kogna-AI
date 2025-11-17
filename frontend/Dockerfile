# ---- Stage 1: The Builder ----
FROM node:18-alpine AS builder
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
FROM node:18-alpine
WORKDIR /app

# Create a non-root user for security
RUN addgroup -S nodejs && adduser -S nodejs -G nodejs
USER nodejs

# Fix 1: Add internal API variable declarations for runtime access
ARG API_URL_INTERNAL
ARG NEXT_PUBLIC_API_URL
ENV API_URL_INTERNAL=${API_URL_INTERNAL}
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Copy only the necessary production files from the 'builder' stage
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Expose the port Next.js runs on
EXPOSE 3000

# Fix 2: Add the command to start the production Next.js server
CMD ["npm", "start"]