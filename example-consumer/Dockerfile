# ----- 1. Jar Building Stage -----
FROM maven:3.6-jdk-11 AS build

# Copy the contents of the src directory
ADD src /usr/src/com.abdulhay.connector/src/

# Copy the project file
COPY pom.xml /usr/src/com.abdulhay.connector

# Install dependencies
RUN apt-get update \
 && apt-get install mosquitto -y \
 && apt-get install mosquitto-clients -y

# Run maven
RUN mvn -f /usr/src/com.abdulhay.connector/pom.xml package -DskipTests

# ----- 2. Image Building Stage -----
FROM openjdk:11

# Set the work directory
WORKDIR /jardir

# Copy the built jar file from the previous stage to the current directory 
COPY --from=build /usr/src/com.abdulhay.connector/target/maven.consumer.hono-0.0.1-SNAPSHOT.jar /jardir

# Set the entry point
ENTRYPOINT ["java", "-jar", "maven.consumer.hono-0.0.1-SNAPSHOT.jar"]

# ----- Docker Command Examples -----

# docker build -t hono-influxdb-connector .
# docker run -p 8080:8080 -t hono-influxdb-connector --hono.client.tlsEnabled=true --hono.client.username=messaging@t20babfe7fb2840119f69e692f184127d --hono.client.password=s9VrzSsOQMzlSKFDgHrj --tenant.id=t20babfe7fb2840119f69e692f184127d --export.ip=influxdb:8086
# docker login --username={$USERNAME} --password={$PASSWORD}
# docker tag hono-influxdb-connector mrki102/hono-influxdb-connector
# docker push mrki102/hono-influxdb-connector
# docker image rm image_id --force
# docker pull mrki102/hono-influxdb-connector