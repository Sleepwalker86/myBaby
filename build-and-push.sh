#!/bin/bash

# Build and Push Script for myBaby Docker Image
# Multi-Architecture Build for Docker Hub
# Usage: ./build-and-push.sh [VERSION]
# Example: ./build-and-push.sh v1.0.1

set -e

DOCKER_USER="sleepwalker86"
IMAGE_NAME="mybaby"

# Version aus Argument oder VERSION-Datei verwenden
if [ -z "$1" ]; then
    VERSION=$(cat "$(dirname "$0")/VERSION" 2>/dev/null)
    if [ -z "$VERSION" ]; then
        echo "❌ Keine Version angegeben und keine VERSION-Datei gefunden."
        exit 1
    fi
    echo "📋 Version aus VERSION-Datei: ${VERSION}"
else
    VERSION="$1"
    # Entferne 'v' Präfix falls vorhanden und füge es wieder hinzu für Konsistenz
    if [[ ! "$VERSION" =~ ^v ]]; then
        VERSION="v${VERSION}"
    fi
fi

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
echo ""
echo "💡 Tipp: Falls 'latest' lokal nicht aktualisiert wird, führe aus:"
echo "   docker pull ${DOCKER_USER}/${IMAGE_NAME}:latest"
echo "   oder lösche den lokalen Cache:"
echo "   docker rmi ${DOCKER_USER}/${IMAGE_NAME}:latest"

