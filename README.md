# cyberlogs
<!-- ABOUT THE PROJECT -->
## About The Project
> A real-time cybersecurity monitoring dashboard that utilizes Kafka log streams in conjunction with FastAPI Processing and React to visualize simulated log activity in real time.

### Built With:

**Frontend**
- [React](https://reactjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [ShadCN UI](https://ui.shadcn.com/)
- [Vite](https://vitejs.dev/)

**Backend:**

- [FastAPI](https://fastapi.tiangolo.com/)
- [Kafka Consumer](https://docs.confluent.io/)
- [MongoDB](https://motor.readthedocs.io/)

**Deployment:**

- [Docker](https://www.docker.com/)
- [Vercel](https://vercel.com/home)
- [Fy.io](https://fly.io) 
<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Environment Setup
Clone Repo
  ```sh
  git clone https://github.com/srmenon02/cyberlogs.git
  cd CyberLogs
  ```
Set up Log Simulator, Kafka Consumer, React front end, and FastAPI
  ```sh
  chmod +x start_all.sh
  .start_all.sh
  ```
###  Usage
Backend
Health Check
  ```sh
  GET /health
  ```
Retrieve Logs
  ```sh
  GET /logs
  ```

Frontend
  ```sh
  https://localhost:5173
  ```

<!-- ROADMAP -->
## Roadmap

- [X] Log-stream input from Kafka
- [X] MongoDB backend
- [X] React UI
- [X] Sort, search, and filter logs by timestamp, level, and message
- [X] Export Logs to CSV
- [X] Docker Deployment
- [ ] User Authentication
- [ ] Log Source Tagging
- [ ] WebSocket live-streaming
- [ ] AI-enabled alert detection

<!-- CONTRIBUTING -->
## Contributing

Any and all contributions are welcome! If you have any suggestions on making improvements, feel free to fork the repo and submit a PR.

<!-- LICENSE -->
## License

Distributed under the project_license. See `LICENSE.txt` for more information.

<!-- CONTACT -->
## Contact

Suraj Menon 
-  Linkedin: www.linkedin.com/in/suraj-menon
-  Email:  srmenon02@gmail.com

