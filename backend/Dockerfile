# Build stage
FROM golang:1.24-alpine AS builder

# Install build dependencies for SQLite (CGO)
RUN apk add --no-cache gcc musl-dev

WORKDIR /app

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy the source code
COPY . .

# Build the application
# CGO_ENABLED=1 is required for go-sqlite3
RUN CGO_ENABLED=1 GOOS=linux go build -o server ./cmd/server/main.go
RUN CGO_ENABLED=1 GOOS=linux go build -o seed ./cmd/seed/main.go

# Final stage
FROM alpine:latest

WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /app/server .
COPY --from=builder /app/seed .

# Create directory for SQLite database
RUN mkdir -p data

# Expose the port
EXPOSE 8080

# Run the executable
CMD ["./server"]