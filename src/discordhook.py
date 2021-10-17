import requests

WEBHOOK_URL = "https://discord.com/api/webhooks/899322150761140244/-Z-09e7kX3YkL0Y87lME7IVtXFBjWKwFdMKH_wRlpWUHSUftYmSujUgtBz28qMxfVOE1"

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

  resp = requests.post(WEBHOOK_URL, json=template)

  return resp.status_code