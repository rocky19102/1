# Solv appointments cloud setup

This workspace is ready to run as a GitHub Actions cloud scheduled job.

## What it does

- Runs every night at 10 PM Pacific time.
- Fetches the Solv search page.
- Checks the tracked clinics.
- Updates the current report files in `outputs/`.
- Appends to `outputs/solv_appointments_history.json`.
- Regenerates the one-column-per-day history CSV and HTML chart.
- Commits the changed output files back to the GitHub repo.

## Files added

- `.github/workflows/solv-appointments-nightly.yml`
- `package.json`

## How to turn it on

1. Create a new GitHub repository.
2. Upload or push this whole folder to the repository, including the `outputs/` folder.
3. In GitHub, open the repository's **Actions** tab.
4. Enable workflows if GitHub asks.
5. Open **Solv appointments nightly report**.
6. Use **Run workflow** once to test it.

After that, GitHub Actions will run it nightly even when your computer is off.

## Where the cloud results live

The cloud job commits updated files back into the repository:

- `outputs/solv_appointments.csv`
- `outputs/solv_appointments.html`
- `outputs/solv_appointments.json`
- `outputs/solv_appointments_history.csv`
- `outputs/solv_appointments_history.html`
- `outputs/solv_appointments_history.json`

GitHub is the cloud storage for the report history. If you want Google Sheets
as the storage/viewing layer later, the next step is adding a Google service
account and Sheets API write step.
