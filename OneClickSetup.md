To run the development server for this project, you should use the Makefile's dev environment targets, which are designed to set up and start everything you need for development (including hot reloading, database, and dependencies).

Here’s how you can do it:

### 1. One-Click Setup (Recommended for First Time)
If this is your first time setting up the project, use:
```sh
make dev-setup
```
- This will check/install required tools, set up Docker containers, and start the dev environment.
- It will prompt you for confirmation before proceeding.

### 2. Start the Dev Environment (Subsequent Runs)
If you’ve already set up the environment before, just run:
```sh
make dev-start
```
- This will start the MongoDB and API dev containers using `docker-compose.dev.yml`.
- The API will be available at: http://localhost:5000

### 3. Useful Dev Commands
- **Stop dev environment:**  
  ```sh
  make dev-stop
  ```
- **View logs:**  
  ```sh
  make dev-logs
  ```
- **Clean dev environment:**  
  ```sh
  make dev-clean
  ```

### What happens under the hood?
- The dev server runs inside a Docker container (`api-dev`) using `nodemon` for hot reloading.
- Your code changes on the host are reflected inside the container thanks to the volume mount (`.:/app`).
- MongoDB runs in a separate container (`mongo-dev`).

Let me know if you want a step-by-step breakdown of what each command does, or if you encounter any issues!