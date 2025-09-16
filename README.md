# Notion Sports Fixture Importer

A set of Python scripts to import sports match fixtures from a CSV file into a structured set of related Notion databases. The script automatically handles creating and linking related items like sports, leagues, seasons, and teams, and prevents creating duplicate entries.

## Features

*   **CSV to Notion**: Imports match data from a `matches.csv` file.
*   **Automated Relations**: Automatically creates and links pages in related Notion databases (Sports, Leagues, Seasons, Teams, Matches).
*   **Smart Caching**: Caches Notion database schemas and created pages to minimize API calls and improve performance.
*   **Duplicate Prevention**: Checks for existing matches based on date and team combination to avoid creating duplicates.
*   **Flexible Date Parsing**: Handles various date and time formats from the input CSV.
*   **Dynamic Properties**: Intelligently builds Notion page properties based on the target database's schema.
*   **Timezone Utility**: Includes a utility script (`changedate.py`) to convert date/time values to different timezones before import.

## Prerequisites

*   Python 3.7+
*   An active Notion account and workspace.

## Setup

Follow these steps to get the project running.

### 1. Install Dependencies

Install the required Python libraries using pip:

```bash
pip install notion-client python-dotenv pandas python-dateutil
```

### 2. Configure Notion

#### A. Create a Notion Integration

1.  Go to My Integrations in your Notion account.
2.  Click **"+ New integration"**.
3.  Give it a name (e.g., "Sports DB Importer") and associate it with your workspace.
4.  Click **"Submit"**.
5.  On the next screen, copy the **"Internal Integration Token"**. You will need this for your environment variables.

#### B. Create and Share Databases

1.  In your Notion workspace, create the following five databases:
    *   `Sports`
    *   `Leagues`
    *   `Seasons`
    *   `Teams`
    *   `Matches`
2.  For each database, click the `...` menu in the top-right corner and select **"+ Add connection"**. Find and select the integration you just created to give it access.
3.  Get the ID for each database. The ID is the long alphanumeric string in the database URL: `https://www.notion.so/your-workspace-name/<DATABASE_ID>?v=...`

### 3. Set Environment Variables

1.  Create a file named `variable.env` in the project's root directory.
2.  Add your Notion token and the database IDs you collected to this file. It should look like this:

```env
NOTION_TOKEN="secret_..."
SPORTS_DB_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
LEAGUES_DB_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
SEASONS_DB_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
TEAMS_DB_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
MATCHES_DB_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

## Usage

### 1. Prepare Your Data

Create a `matches.csv` file in the same directory. The script expects the column headers listed below. or YOU CAN MAIL ME FOR DETAILED STRUCTURE

#### `matches.csv` File Format

| Header              | Type   | Description                                                              | Required |
| ------------------- | ------ | ------------------------------------------------------------------------ | -------- |
| `name`              | Text   | The name of the match (e.g., "Team A vs Team B").                        | **Yes**  |
| `date`              | Text   | The date and time of the match. Various formats are supported.           | **Yes**  |
| `sport`             | Text   | The name of the sport (e.g., "Football").                                | **Yes**  |
| `league`            | Text   | The name of the league (e.g., "Premier League").                         | **Yes**  |
| `season`            | Text   | The season identifier (e.g., "2023-2024").                               | **Yes**  |
| `home team`         | Text   | The name of the home team.                                               | **Yes**  |
| `away team`         | Text   | The name of the away team.                                               | **Yes**  |
| `match type`        | Text   | The type of match (e.g., "League", "Cup"). Must match a Select option in Notion. | **Yes**  |
| `home score`        | Number | The final score for the home team.                                       | No       |
| `away score`        | Number | The final score for the away team.                                       | No       |
| `result`            | Text   | A text description of the result.                                        | No       |
| `prediction`        | Text   | Any prediction text for the match.                                       | No       |
| `conductor numeral` | Number | An optional numeric identifier for the match.                            | No       |

### 2. Run the Import Script

The main, most up-to-date script is `uploadwithMatchNumber.py`. Execute it from your terminal:

```bash
python uploadwithMatchNumber.py
```

The script will read `matches.csv`, process each row, and create the corresponding pages in your Notion databases, printing its progress to the console.

## Utility Script: `changedate.py`

This script helps you convert a list of dates from UTC to a specific timezone, which can be useful for preparing your `matches.csv`.

**Usage:**
1.  Create a `dates.csv` file with a single column named `datetime`.
2.  Run the script: `python changedate.py`.
3.  Follow the on-screen prompts to select your target timezone from the list.
4.  The results will be saved in `outputdates.csv` with formats suitable for Notion and Google Sheets.
