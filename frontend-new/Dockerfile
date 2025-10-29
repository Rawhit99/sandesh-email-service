# Multi-stage build for production optimization
FROM node:18-alpine AS builder

WORKDIR /app

# Accept build arguments for React environment variables
ARG REACT_APP_API_URL=http://localhost:8000

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies with optimizations
RUN npm ci --only=production --silent && npm cache clean --force

# Copy source code
COPY . .

# Set environment variables for build
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine AS production

# Copy built assets from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

