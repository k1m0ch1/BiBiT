from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/")
async def index():
    html_content =  """
    <html>
        <body>
            Hi! Welcome to BiBiT API, the yogyaonline, alfacart and klikindomaret API
            <br/><br/>
            available API :
            <br/>- yogyaonline catalog <a href='https://bibit-api.yggdrasil.id/yogyaonline/catalog'>https://bibit-api.yggdrasil.id/yogyaonline/catalog</a>
            <br/>- yogyaonline catalog available date <a href='https://bibit-api.yggdrasil.id/yogyaonline/catalog/available'>https://bibit-api.yggdrasil.id/yogyaonline/catalog/available</a>
        </body>
    </html>
    """

    return HTMLResponse(content=html_content, status_code=200)
