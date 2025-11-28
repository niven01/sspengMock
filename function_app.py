import azure.functions as func
import logging
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        if req.method == 'GET':
            return func.HttpResponse(
                json.dumps({"message": "MockApiFunction is working!", "method": "GET"}),
                status_code=200,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
        else:
            # Handle POST and other methods
            body = None
            try:
                body = req.get_json()
            except:
                try:
                    body = req.get_body().decode('utf-8')
                except:
                    body = None
            
            response = {
                "message": "Request captured!",
                "method": req.method,
                "body": body,
                "query": dict(req.params),
                "headers": dict(req.headers)
            }
            
            return func.HttpResponse(
                json.dumps(response, indent=2),
                status_code=200,
                mimetype="application/json",
                headers={"Access-Control-Allow-Origin": "*"}
            )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            headers={"Access-Control-Allow-Origin": "*"}
        )