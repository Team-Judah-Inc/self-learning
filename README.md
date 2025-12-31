# Self Learning Project

This repository contains the source code for the Self Learning project, consisting of a backend, frontend, and mock bank services.

## Project Purpose

This project mocks a system that connects to bank and credit accounts, allowing users to view their transactions. It provides tips on how to save money, similar to the RiseUp style.

## Running with Docker Compose

The project includes a `docker-compose.yml` file in the root directory to easily run the backend service.

### Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your machine.

### Instructions

1.  **Start the services:**

    Run the following command in the root directory to build and start the containers:

    ```bash
    docker-compose up --build
    ```

    The `--build` flag ensures that the Docker image is rebuilt if there are any changes to the source code.

2.  **Access the Backend:**

    Once the container is running, the backend service will be available at:
    `http://localhost:8080`

3.  **Stop the services:**

    To stop the running containers, you can press `Ctrl+C` in the terminal where the logs are streaming.
    
    To remove the containers and network, run:

    ```bash
    docker-compose down