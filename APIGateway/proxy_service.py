from fastapi import FastAPI, HTTPException, Request, Depends
import requests
from fastapi.security import OAuth2PasswordBearer
from config import settings

app = FastAPI()
app.title = "API Router"
  

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

@app.post("/register")
async def register(request: Request):
    data = await request.json()
    resp = requests.post(f"{settings.USER_SERVICE_URL}/register", json=data)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@app.post("/token")
async def token(request: Request):
    form = await request.form()
    resp = requests.post(f"{settings.USER_SERVICE_URL}/token", data=form)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@app.get("/profile")
async def get_profile(request: Request, token: str = Depends(oauth2_scheme)):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{settings.USER_SERVICE_URL}/profile", headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@app.put("/profile")
async def update_profile(request: Request, token: str = Depends(oauth2_scheme)):
    headers = {"Authorization": f"Bearer {token}"}
    data = await request.json()
    resp = requests.put(f"{settings.USER_SERVICE_URL}/profile", headers=headers, json=data)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

