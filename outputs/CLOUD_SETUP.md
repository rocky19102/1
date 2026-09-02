# Solv Appointments Cloud Setup

This folder is ready to run as a GitHub Actions scheduled job. GitHub will run the report in the cloud and commit the updated result files back into the repository.

## What It Does

- Runs the Solv appointment report every night at 10 PM Pacific time.
- Saves the current report files in `outputs/`.
- Updates the daily history files with one column per day.
- Keeps the data in cloud storage by committing the updated files to the GitHub repository.

## Files To Keep In GitHub

- `.github/workflows/solv-appointments-nightly.yml`
- `package.json`
- `outputs/solv_appointments_report.js`
- `outputs/solv_appointments.csv`
- `outputs/solv_appointments.html`
- `outputs/solv_appointments.json`
- `outputs/solv_appointments_history.csv`
- `outputs/solv_appointments_history.html`
- `outputs/solv_appointments_history.json`

## One-Time GitHub Setup

1. Create a new private GitHub repository.
2. Push this whole folder to that repository.
3. Open the repository on GitHub.
4. Go to `Actions`.
5. Enable workflows if GitHub asks.
6. Open `Solv appointments nightly report`.
7. Click `Run workflow` once to test it.

After that, GitHub will run it every night at 10 PM Pacific.

## Where Results Will Be

The cloud results will be in the repository under:

- `outputs/solv_appointments_history.html`
- `outputs/solv_appointments_history.csv`
- `outputs/solv_appointments_history.json`

The workflow commits those files after each successful run, so the repository becomes the cloud storage location.

## Optional Upgrade Later

If you want the results in a live Google Sheet instead of GitHub files, add a Google service account and store its credentials as a GitHub Actions secret. The report script can then be extended to append each daily run to that sheet.
