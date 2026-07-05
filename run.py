"""
Entry point for PhotoBridge.
Starts uvicorn server bound to 0.0.0.0 so phones on the LAN can reach it.
"""

import uvicorn
from app.config import get_port_from_env


if __name__ == "__main__":
    port = get_port_from_env()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="warning"
    )

