FROM gradle:8.14.3-jdk21 AS build
WORKDIR /workspace
COPY . .
RUN ./gradlew bootJar --no-daemon

FROM eclipse-temurin:21-jre-alpine
RUN apk add --no-cache curl \
    && addgroup -S cafe \
    && adduser -S -G cafe cafe
WORKDIR /app
COPY --from=build --chown=cafe:cafe /workspace/build/libs/*.jar application.jar
USER cafe
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/application.jar"]
