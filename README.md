# comfyui-api-gateway

Hacked together API gateway for ComfyUI as there isn't really a usable API out of the box.

### Installing
`poetry install`

### Running
`<ENV VARS> poetry run uvicorn app:app`

### Getting a workflow file
In ComfyUI, hit the gear icon next to the queue size and enable dev mode. Then, hit the "Save (API Format)" button.

### Config
Configurationi is done via environment variables:

Auth:
* `USERNAME`: Basic auth username
* `PASSWORD`: Basic auth password

Workflow:
* `WORKFLOW_PATH`: Path to workflow JSON
* `COMFYUI_URL`: URL to ComfyUI instance
* `CLIENT_ID`: Client ID for API
* `POSITIVE_PROMPT_INPUT_ID`: Input ID of the workflow where there is a text field for the positive prompt
* `NEGATIVE_PROMPT_INPUT_ID`: Input ID of the workflow where there is a text field for the negative prompt
* `SEED_PROMPT_INPUT_ID`: Input ID of the workflow where there is a field for the seed

### Usage
Example cURL:

`curl -X POST 'http://user:pass@127.0.0.1:8000/generate?positive_prompt=dog&negative_prompt=text&seed=-1'`

You'll get back JSON with base64 encoded images.
