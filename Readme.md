## run
```
$> uvicorn app:app --reload
```
$> uvicorn app:app --workers 1 --host 0.0.0.0 --port 8087 --reload

source venv/bin/activate

pip freeze > requirements.txt

pip install --upgrade pip

pip install --no-cache-dir -r requirements.txt


# TEST

```json
curl -X 'POST' \
  'http://localhost:8087/extractor' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer dev' \
  -H 'Content-Type: application/json' \
  -d '{
  "sentence": "test"
}'


curl -X 'GET' \
  'http://localhost:8087/extractor?page_start=1&page_size=10' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer dev'
```