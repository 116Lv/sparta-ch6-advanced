FROM gradle:8.14.3-jdk21 AS build
WORKDIR /workspace
COPY . .
RUN ./gradlew bootJar --no-daemon

FROM eclipse-temurin:21-jre-alpine
RUN apk add --no-cache curl
WORKDIR /app
COPY --from=build /workspace/build/libs/*.jar application.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/application.jar"]
