import uvicorn
from dm_email_owner_svc.app import app
from dm_email_owner_svc.config import SERVICE_PORT
from dm_email_owner_svc.core.logging import configure_logging


def main():
    # Configure non-blocking logging before starting the server
    configure_logging()
    service_port = int(SERVICE_PORT)
    uvicorn.run(app, host="0.0.0.0", port=service_port)


if __name__ == "__main__":
    main()