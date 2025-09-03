from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field


class PushNotification(BaseModel):
    """The message to be sent to the user"""
    argument: str = Field(..., description=" The message to be sent to the user")

class PushNotificationTool(BaseTool):
    name: str = "Push Notification Tool"
    description: str = (
        "This tools is used to send the push notification to the user"
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        pushover_user = os.getenv("PUSHOVER_USER")
        pushover_token = os.getenv("PUSHOVER_TOKEN")
        pushover_url= os.getenv("PUSHOVER_URL")

        print(f"push :{message}")

        payload = {"user":pushover_user, "token": pushover_token, "message": message }
        requests.post(pushover_url, data = payload)
        return {"satatus":"success"}
  
