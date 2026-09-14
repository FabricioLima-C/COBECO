import asyncio

from starlette.responses import JSONResponse


class RequestLimits:
    """Bound streamed bodies before JSON decoding, including bodies without Content-Length."""

    def __init__(self, app, maximum=65536, timeout=10):
        self.app, self.maximum, self.timeout = app, maximum, timeout

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
            if length < 0:
                raise ValueError()
        except ValueError:
            return await self.reject(scope, receive, send, 400, "Tamanho de requisição inválido.")
        if length > self.maximum:
            return await self.reject(scope, receive, send, 413, "Requisição muito grande.")
        body = bytearray()
        try:
            async with asyncio.timeout(self.timeout):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    chunk = message.get("body", b"")
                    if len(body) + len(chunk) > self.maximum:
                        return await self.reject(scope, receive, send, 413, "Requisição muito grande.")
                    body.extend(chunk)
                    if not message.get("more_body", False):
                        break
        except TimeoutError:
            return await self.reject(scope, receive, send, 408, "Tempo de envio esgotado.")
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)

    @staticmethod
    async def reject(scope, receive, send, status, message):
        response = JSONResponse(
            {"error": {"code": "REQUEST_LIMIT", "message": message}},
            status,
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )
        await response(scope, receive, send)
