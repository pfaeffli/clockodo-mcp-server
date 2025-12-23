# Testing Clockodo Functions in Jupyter Notebook

This guide explains how to test the Clockodo client functions using the provided Jupyter notebook in Docker.

## Quick Start

1. **Start the Jupyter notebook server:**
   ```bash
   make manual-test
   ```

   Or directly with docker-compose:
   ```bash
   docker-compose -f docker-compose.test.yml up jupyter
   ```

2. **Open your browser:**
   - Navigate to `http://localhost:8888`
   - The notebook will open without requiring a token/password

3. **Open the test notebook:**
   - In JupyterLab, navigate to `work/manual-test/test_clockodo.ipynb`
   - The project directory is mounted at `/home/jovyan/work`

4. **Configure your credentials:**
   - In the second cell, replace the placeholder values with your actual Clockodo API credentials:
     ```python
     os.environ['CLOCKODO_API_USER'] = 'your-email@example.com'
     os.environ['CLOCKODO_API_KEY'] = 'your-api-key'
     ```

5. **Run the tests:**
   - Execute each cell sequentially (Shift + Enter)
   - Or use "Run > Run All Cells" to run everything at once

## What the Notebook Tests

The notebook includes several test sections:

1. **List Users** - Tests the `list_users()` function
2. **Get User Reports** - Tests the `get_user_reports()` function for the current year
3. **Different Type Levels** - Tests user reports with different aggregation levels (0-3)
4. **User-Specific Reports** - Tests fetching reports for a specific user ID
5. **Debug Tool Function** - Tests the actual debug tool from `debug_tools.py`
6. **HTTP Headers Inspection** - Shows what headers are being sent
7. **Multiple Years** - Tests fetching reports across different years

## Stopping the Server

```bash
docker-compose -f docker-compose.test.yml down jupyter
```

## Troubleshooting

- **Port 8888 already in use**: Change the port mapping in `docker-compose.test.yml` from `"8888:8888"` to `"8889:8888"` (or any available port)
- **Permission issues**: The notebook runs as user `jovyan` inside the container, which should have access to the mounted volume
- **Import errors**: Make sure the notebook is run from the correct location so the `sys.path` modification can find the `src` directory

## Environment Variables

You can also set credentials via environment variables before starting Docker:

```bash
export CLOCKODO_API_USER='your-email@example.com'
export CLOCKODO_API_KEY='your-api-key'
make manual-test
```

Then modify the notebook to use these instead of hardcoding them.
