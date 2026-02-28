# JW Publisher Transfer Tool

A web-based tool for extracting individual publisher records from an [Hourglass](https://www.hourglass-app.com/en/) JSON export so they can be transferred to another congregation using [NW Scheduler](https://nwscheduler.com/) or similar tools.

## The Problem

Hourglass exports **all** publisher records in a single JSON file. When you need to send just one publisher's card to another congregation, you'd have to manually locate and extract that publisher's data block plus their associated field service reports. This tool automates that process.

## Privacy & Security

**All data processing happens entirely in your browser.** No publisher information -- names, addresses, phone numbers, field service reports -- is ever sent to any server. The server's only job is to serve the HTML page itself. Even if hosted in the cloud, your congregation's PII never leaves your computer.

## How It Works

1. **Upload** your full Hourglass JSON export (parsed locally in your browser)
2. **Select** one or more publishers from a searchable, sortable list
3. **Download** a filtered JSON file containing only the selected publishers and their reports

The exported file is formatted for NW Scheduler's Hourglass import, including all required sections (congregation, publishers, addresses, reports, privileges, etc.).

## Quick Start

### Prerequisites

- Python 3.10+

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload

# Open http://localhost:8000 in your browser
```

### Run with Docker

```bash
# Build the image
docker build -t jw-publisher-transfer .

# Run the container
docker run -p 8000:8000 jw-publisher-transfer
```

Then visit [http://localhost:8000](http://localhost:8000).

## Cloud Deployment

The included `Dockerfile` makes this ready for deployment on any Docker-compatible platform:

- [Railway](https://railway.app/)
- [Render](https://render.com/)
- [Fly.io](https://fly.io/)
- Any cloud provider with container support

Since all processing is client-side, the server has no access to publisher data regardless of where it is hosted.

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app (serves page only)
│   └── templates/
│       └── index.html      # Single-page UI with all processing logic
├── static/
│   └── style.css           # Custom styles
├── requirements.txt
├── Dockerfile
└── README.md
```

## Tech Stack

- **FastAPI** -- Serves the static page
- **Tailwind CSS** -- Styling (via CDN)
- **Vanilla JavaScript** -- All data parsing, filtering, and export logic runs in the browser
- No database required -- fully stateless, zero server-side data processing
