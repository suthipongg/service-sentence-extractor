module.exports = {
    "apps": [{
        "name": "service-sentence-extractor",
        "script": "uvicorn app:app --workers 1 --host 0.0.0.0 --port 8087",
        "instances": "1",
        "output": "./logs/my-app-out.log",
        "error": "./logs/my-app-error.log"
    }]
}
