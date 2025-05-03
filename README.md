# Face Recognition Attendance System

A comprehensive web-based attendance system using facial recognition technology, powered by DeepStack AI.

## Quick Setup Guide

### 1. Setting Up DeepStack AI Docker Container

DeepStack is the AI engine that powers the face recognition functionality in this system. Here's how to set it up:

```bash
# Pull the DeepStack AI image
docker pull deepquestai/deepstack

# Run the DeepStack container with face recognition enabled
docker run -e VISION-FACE=True -v localstorage:/datastore -p 5000:5000 deepquestai/deepstack
```

The container will start running, and you should see output indicating the server is ready. DeepStack will be accessible at `http://localhost:5000`.

### 2. Verifying DeepStack is Running

To check if DeepStack is running correctly:
```bash
curl http://localhost:5000/v1/vision/detection
```

If DeepStack is running, you should get a JSON response.

### 3. Setup the Flask Application

```bash
# Install required dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Access the application at `http://localhost:5000` in your web browser.

## Alternative: Using Docker Compose (Complete Setup)

For easier setup of both DeepStack and the web application:

1. Ensure Docker and Docker Compose are installed
2. Run the following command in the project directory:

```bash
docker-compose up
```

This will start both DeepStack and the web application containers. The web application will be accessible at `http://localhost:8000`.

## Troubleshooting DeepStack

### Common Issues:

1. **Port conflict**: If port 5000 is already in use, change the port mapping in the docker run command:
   ```bash
   docker run -e VISION-FACE=True -v localstorage:/datastore -p 5001:5000 deepquestai/deepstack
   ```
   Then update the `DEEPSTACK_URL` in app.py to use the new port.

2. **Container not starting**: Check Docker logs:
   ```bash
   docker ps -a  # Find container ID
   docker logs [container_id]
   ```

3. **Face recognition not working**: DeepStack needs time to initialize its models on first run. Wait a few minutes after starting the container before testing.

## DeepStack Container Management

```bash
# List all containers
docker ps -a

# Stop the DeepStack container
docker stop [container_id]

# Restart the container
docker restart [container_id]

# Remove the container (data will be preserved in the volume)
docker rm [container_id]
```

## System Requirements

- Docker Engine 19.03.0+
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Internet connection (for initial setup)