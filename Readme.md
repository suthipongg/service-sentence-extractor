<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="https://img5.pic.in.th/file/secure-sv1/Untitled5349eaa69a042138.png" alt="search database logo"></a>
</p>

<h3 align="center">Sentence Extractor Service</h3>

---

<p align="center">sentence to embedded vector
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Features](#features)
- [Getting Started](#getting_started)
- [Running the tests](#tests)
- [Deployment](#deployment)
- [Usage](#usage)
- [Authors](#authors)
- [VERSION](#version)

## 🧐 About <a name = "about"></a>

**Sentence Extractor Service** project is designed to process text, extract sentences, and convert them into embedded vectors using state-of-the-art natural language processing (NLP) techniques. This service is useful for various applications such as text analysis, semantic search, document similarity, and more.

## ✨ Features <a name = "features"></a>

- **Sentence Embedding:** Extracts sentences from the input text into a high-dimensional vector representation.
- **Batch Processing:** Handles multiple texts in a single request for efficient processing.
- **Customizable Embedding Models:** Supports different embedding models to suit various use cases.
- **Token Count:** Counts the number of tokens for each sentence as processed by the embedding model.
- **Model Warmup:** Warms up the model to improve initial inference time.

## 🏁 Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.

### Prerequisites

Make sure you have the following software installed:

- [GitHub Project](https://github.com/Nawaphong-13/Service-sentence-extractor)
- [Python3](https://www.python.org/)
- [pm2](https://pm2.keymetrics.io/docs/usage/quick-start/)
- [Elasticsearch](https://www.elastic.co/) (version 7.17.x)
- [MongoDB](https://www.mongodb.com/)
- [Sentence Transformers](https://sbert.net/docs/sentence_transformer/pretrained_models.html#multilingual-models) (current model -> [paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2))

### Multilingual Models
Models | Dimensions | Size(MB) | Suitable Score Functions | Speed(sentence/sec in V100) | Performance Semantic Search(Higher=Better)
---|---|---|---|---|---
[paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2) (Recommended)| 384 | 420 | cosine-similarity | 7500 | 39.19
[paraphrase-multilingual-mpnet-base-v2](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2) | 768 | 970 | cosine-similarity | 2500 | 41.68

### Installation

1. Clone this GitHub repository:
  ```bash
  git clone https://github.com/Nawaphong-13/Service-sentence-extractor
  ```

2. Create a virtual environment:
  ```bash
  python3 -m venv venv
  ```

3. Activate the virtual environment:
  ```bash
  # For Linux
  source venv/bin/activate
  ```

4. Install the required packages from the requirements file:
  ```bash
  pip install -r requirements.txt
  ```

5. Run service
  ```bash
  uvicorn app:app --workers 1 --host 0.0.0.0 --port 8087 --reload
  ```

## 🔧 Running the tests <a name = "tests"></a>

To run the automated tests for this system, follow these steps:

1. Navigate to the GitHub project directory:
  ```bash
  cd test_api
  ```

2. Run test for the GitHub project:
  ```bash
  bash test_api.bash 
  ```

3. Test sentence extractor
  ```bash
  curl -X 'POST' \
    'http://localhost:8087/extractor' \
    -H 'accept: application/json' \
    -H 'Authorization: Bearer dev' \
    -H 'Content-Type: application/json' \
    -d '{
    "sentence": "test"
  }'
  ```

4. Test display history sentence extracted
  ```bash
  curl -X 'GET' \
    'http://localhost:8087/extractor?page_start=1&page_size=10' \
    -H 'accept: application/json' \
    -H 'Authorization: Bearer dev'
```

## 🎈 Usage <a name="usage"></a>

To use the system, follow these steps:

1. **Run the application:**
  ```bash
  bash start_pm2.sh
  ```

2. **Access the application:**
    Open your browser and navigate to `http://localhost:8087`

This section provides clear instructions for running the UVicorn servers for this project. Adjust it as needed based on your project's specifics.

## 🚀 Deployment <a name = "deployment"></a>

1. **Server Setup**: Set up a server environment suitable for hosting your project. This typically involves choosing a cloud provider and provisioning a virtual machine instance.

2. **Software Installation**: Install the necessary software dependencies on your server, including Python. Follow the installation instructions provided by the respective software vendors.

3. **Clone Repository**: Clone the GitHub repository containing your project onto your server using the `git clone` command.

4. **Environment Configuration**: Set up environment variables and configuration files as needed for your project. Ensure that sensitive information such as API keys and database credentials are securely stored.

5. **Build and Install**: Build your project and install any required dependencies using the appropriate package manager (e.g., pip for Python projects). You may also need to compile any frontend assets if applicable.

6. **Run Servers**: Start the necessary servers for your project, such as UVicorn for running your web application and any other backend services (e.g., Elasticsearch, MongoDB, Redis).

<details>
<summary>Version</summary>

# Version History

## [0.0.1] (2024-07-23)
### Added
- GPU usage condition.
### Fixed
- Pydantic model type issue: now uses `datetime`.

## [0.0.0] (2024-07-05)
### Added
- Initial release of the project.

</details>