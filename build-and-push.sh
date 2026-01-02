#!/bin/bash

# Build and Push Script for myBaby Docker Image
# Multi-Architecture Build for Docker Hub

set -e

DOCKER_USER="sleepwalker86"
IMAGE_NAME="myBaby"
VERSION="v1.0.0"

echo "🚀 Building and pushing ${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"

# Prüfe ob Docker Buildx verfügbar ist
if ! docker buildx version > /dev/null 2>&1; then
    echo "❌ Docker Buildx ist nicht verfügbar. Bitte installiere es zuerst."
    exit 1
fi

# Erstelle einen neuen Builder für Multi-Architecture (falls noch nicht vorhanden)
BUILDER_NAME="mybaby-builder"
if ! docker buildx inspect $BUILDER_NAME > /dev/null 2>&1; then
    echo "📦 Erstelle neuen Buildx Builder: $BUILDER_NAME"
    docker buildx create --name $BUILDER_NAME --use
else
    echo "📦 Verwende vorhandenen Buildx Builder: $BUILDER_NAME"
    docker buildx use $BUILDER_NAME
fi

# Starte den Builder
docker buildx inspect --bootstrap

# Build und Push für Multi-Architecture (amd64, arm64)
echo "🔨 Baue Multi-Architecture Image..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag ${DOCKER_USER}/${IMAGE_NAME}:${VERSION} \
    --tag ${DOCKER_USER}/${IMAGE_NAME}:latest \
    --push \
    .

echo "✅ Build und Push erfolgreich abgeschlossen!"
echo "📦 Image verfügbar als:"
echo "   - ${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
echo "   - ${DOCKER_USER}/${IMAGE_NAME}:latest"

