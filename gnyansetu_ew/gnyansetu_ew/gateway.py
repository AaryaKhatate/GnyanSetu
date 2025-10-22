from fastapi import FastAPI, Request
import httpx

app = FastAPI(title="GnyanSetu Gateway")

SERVICES = {
    'lesson': 'http://localhost:8081',
    'visualization': 'http://localhost:8082',
    'quiz': 'http://localhost:8083'
}

@app.get('/health')
async def health():
    return {'status': 'ok', 'services': SERVICES}

@app.post('/api/generate-lesson/')
async def proxy_generate_lesson(request: Request):
    # Proxy multipart upload to lesson service
    async with httpx.AsyncClient() as client:
        content = await request.body()
        headers = dict(request.headers)
        resp = await client.post(f"{SERVICES['lesson']}/api/generate-lesson/", content=content, headers=headers)
        return resp.json()

@app.api_route('/api/{service}/{path:path}', methods=['GET','POST','DELETE'])
async def generic_proxy(service: str, path: str, request: Request):
    if service not in SERVICES:
        return {'error': 'service not found'}
    url = f"{SERVICES[service]}/api/{path}"
    async with httpx.AsyncClient() as client:
        method = request.method
        content = await request.body()
        headers = dict(request.headers)
        resp = await client.request(method, url, content=content, headers=headers)
        return resp.json()
