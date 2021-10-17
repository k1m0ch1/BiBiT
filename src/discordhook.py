import requests
import config

def sendMessage(content: str, title: str, description: str):
  template = {
    "content": content,
    "embeds": [
      {
        "title": title,
        "description": description
      }
    ]
  }

  resp = requests.post(config.WEBHOOK_DISCORD_URL, json=template)

  return resp.status_code