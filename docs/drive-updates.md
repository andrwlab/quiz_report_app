# Updating Quiz Status from a shared Drive folder

The `google_drive_folder` backend is opt-in. The current `google_sheets` backend remains available. The original report generator on `main` is unaffected.

## Format confirmed with the supplied source

- Import only tabs named `Week N`. All other tabs are ignored, as approved by the user.
- Subjects are section headings immediately before a table header with `Grade`, `Quiz #`, `No Attempts`, `Low Scores`.
- Grade cells may be merged vertically: a following quiz row inherits the grade until the next subject section.
- `No Attempts` maps to Pending; `Low Scores` maps to Low Score. Codes are preserved literally, including their academic-year prefixes and internal spacing. Weeks come from tab names.
- Explicit source separators are commas, semicolons, newlines and standalone `and` / `y`. Score annotations are removed from student labels. Free-text notes, merged names and misspellings are not guessed.
- Accents, capitalization and periods are normalized. A first name, surname or initial abbreviation must uniquely identify one official student within the grade. Combined grades such as G9 search both official sections. Ambiguity blocks publication.

`Students` is the authoritative roster with Student Number, Student Name, Group. `Aliases` provides approved mappings with headers Grade, Subject, Report Name, Student Number. Subject is optional; blank means the alias applies across that grade. Use aliases only for one actual student, never to turn a prose note or multiple merged names into one identity.

## One-time configuration

1. Enable Google Drive API in the service account's Google Cloud project.
2. Share the update folder with the existing service-account email as **Reader**. Professors who replace the source file need **Editor** on the folder.
3. Give that service account **Editor** on the private publication spreadsheet. It writes only the Quizzes and Publication tabs; it never edits or deletes the upload or official roster.
4. In Secrets of the **Quiz Status** app, set these top-level keys before `[gcp_service_account]`:

```toml
SABIS_STORAGE = "google_drive_folder"
SABIS_SPREADSHEET_ID = "PRIVATE_SPREADSHEET_ID"
QUIZ_SOURCE_FOLDER_ID = "PRIVATE_FOLDER_ID"
```

Keep the existing service-account section. No real IDs, student data or credentials belong in GitHub. The broader Sheets OAuth scope is selected only for the opt-in Drive backend; the existing Sheets backend remains read-only.

The backend checks updates at most once every 60 seconds, when the Streamlit interface runs again (search, filter or reload). It does not run a separate scheduled job while the app is idle or asleep. Changing, replacing or deleting a file is detected by folder contents, file ID and MD5 checksum; the filename can change.

## Publication guarantees

The folder must contain exactly one `.xlsx` file. The backend validates every weekly identity and status before writing. File checksum, roster and aliases are rechecked before publication to detect changes during import. Only then does one atomic Google Sheets batch replace Quizzes and publication metadata. Student Numbers remain text. A source hash avoids reprocessing an unchanged version. A publication with no Pending or Low Score records is permitted only when the workbook contains actual valid weekly quizzes.

An empty folder, two XLSX files, invalid names, failed permissions or an incomplete upload keeps the last successful snapshot. After a Streamlit restart, the persistent Quizzes tab is the fallback, so replacing/deleting the Excel cannot erase the last valid published data. Apps show an update-unavailable notice while using that fallback. The date is taken from successful publication metadata in the Drive backend.

## Source review before activation

The first uploaded source was parsed locally in about 0.35 seconds, excluding download. It contains 416 quiz rows across Week 2–12. Validation found 42 distinct unresolved names/notes across 176 mentions; these are review cases, not a count of missing students. Review them in the private `Import Review` tab. They include students absent from the roster, abbreviated/merged names, ambiguous first names and notes instead of names. No partial import was published.

Fix the source or official roster, or add confirmed one-student mappings in Aliases. Regenerate a review with `review_weekly_workbook()` as needed. Until those cases are resolved and the Drive permissions/API are configured, keep the hosted app on `google_sheets`.

## Tests

Run `python -m unittest discover -s tests -v`. Synthetic fixtures verify merged-grade reading, exact quiz codes, names and scores, approved aliases, ambiguous/missing identities, formula rejection, empty and duplicate uploads, stable-version checks, atomic publication and restart fallback. No real student identities are stored in test fixtures.
