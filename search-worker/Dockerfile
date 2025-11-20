# Build stage
FROM golang:1.25-alpine AS builder

WORKDIR /app

COPY go.mod ./ 
COPY go.sum ./

RUN go mod download

COPY . ./

RUN go build -o /app/main .

# Final stage
FROM alpine:latest

WORKDIR /app

COPY --from=builder /app/main .

EXPOSE 50053

CMD ["./main"] 
