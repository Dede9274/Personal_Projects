# Digital Archive Scanner

A local-first Python service that extracts text from scanned PDFs, classifies each document, and copies the untouched original into the correct archive folder.

The first milestone supports three categories:

- invoices (`invoice`)
- receipts (`receipt`)
- delivery notes (`delivery_note`)
- uncertain documents (`needs_review`)

## 1. Install the prerequisites

Python 3.11, Git, and Tesseract OCR are required.

Install a Windows Tesseract build with both German and English language data, then open a new PowerShell window and verify:

```powershell
tesseract --version
tesseract --list-langs
```

The language list must include:

```text
deu
eng
sqi
```

## 2. Create the Python environment

From this project directory:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If PowerShell blocks activation, run this once in the current terminal and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3. Process one test PDF

Use a synthetic or non-confidential PDF:

```powershell
smart-archive samples\test_invoice.pdf
```

You can also run the package directly:

```powershell
python -m smart_archive samples\test_invoice.pdf
```

For Albanian and English scans:

```powershell
smart-archive samples\test_invoice.pdf --languages sqi+eng
```

Example output:

```text
File: test_invoice.pdf
Text extraction: OCR (deu+eng)
Prediction: invoice
Confidence: 100%
Destination: data\archive\invoices\test_invoice.pdf
```

Digital PDFs with embedded text do not require OCR. Image-only scans are rendered at 300 DPI and passed to Tesseract.

## 4. Run the tests

```powershell
python -m pytest
```

## 5. Monitor incoming scans automatically

Start the watcher from the project directory:

```powershell
smart-archive-watch --languages sqi+deu+eng --max-attempts 3 --retry-delay 2
```

Keep that terminal open. The watcher processes existing PDFs and new PDFs placed in:

```text
data\incoming\
```

For each PDF, it:

1. Waits until the file size and modification time stop changing.
2. Confirms no writer holds the file open and verifies the PDF header, EOF marker, and structure.
3. Moves the completed PDF into `data\processing`.
4. Calculates its SHA-256 checksum and checks `data\smart_archive.db`.
5. Preserves repeated content in `data\duplicates` instead of archiving it twice.
6. Records each processing attempt in `data\smart_archive.db` so retry counts survive restarts.
7. Runs OCR and classification for new content, retrying transient failures with increasing delays.
8. Copies it into the correct archive folder or `needs_review`.
9. Removes the staged copy only after verifying the archived copy and recording its checksum.
10. Moves the PDF from `processing` to `failed` only after all attempts are exhausted.
11. Writes activity, retries, failures, and recovery actions to rotating logs in `data\logs`.

Stop the watcher with `Ctrl+C`. The original file leaves `incoming` only after it is stable, and a successful archive copy is preserved before the staged file is removed.

The active log is `data\logs\smart_archive.log`. When it reaches 5 MB, the program rotates it and keeps up to five older log files.

Follow the log live from another PowerShell window:

```powershell
Get-Content data\logs\smart_archive.log -Wait
```

After an unexpected shutdown, restart `smart-archive-watch`. It automatically queues PDFs left in `data\processing`, continues their saved attempt counts, removes incomplete temporary archive copies, and recognizes archive copies completed immediately before the crash. Completed copies are finalized instead of archived or marked as duplicates a second time.

Retry one failed PDF by its name:

```powershell
smart-archive-retry broken.pdf
```

Retry every PDF in `data\failed`:

```powershell
smart-archive-retry
```

The retry command resets the saved attempt count and moves each selected PDF back to `data\incoming`. A running watcher detects it immediately; otherwise, the watcher processes it the next time it starts. Use `--archive-root` with both commands if your data directory is somewhere else.

## Project layout

```text
Digital_Archive_Scanner/
├── data/
│   ├── incoming/
│   ├── processing/
│   ├── archive/
│   ├── needs_review/
│   ├── duplicates/
│   ├── failed/
│   └── logs/
├── samples/
├── src/smart_archive/
└── tests/
```

Do not place real confidential company documents in Git. The next milestone is configuring the Océ CS231 to send scans into `data/incoming` using its existing scan-to-SMB or scan-to-FTP feature.
