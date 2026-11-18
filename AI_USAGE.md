# AI Usage

## Tool I used

I used **Claude Code** (Claude Opus 5.5), an AI coding assistant that runs in my terminal.

## What I asked it to do

1. Create a Flask app on my `job_tracker` MySQL database. It needed add, view, edit and delete pages for all four tables, HTML templates, a Job Match feature that shows skill match percentages, and testing.

## How I used it

- **Getting started:** It read my existing Python scripts and checked the real table structure in MySQL. My MySQL service was stopped, so I approved a Windows admin prompt to start it.
- **Database:** My tables had no JSON column, so I had it add a `requirements` JSON column to `jobs`. This column holds each job's required skills. It backed up the database first.
- **Code:** It wrote the Flask routes for all four tables, the form validation, the HTML templates and the Job Match logic.
- **Testing:** It wrote 74 automated tests. They run on a separate test database, so my real data isn't touched.

## Problems we fixed

- MySQL wasn't running, so I started the service as admin.
- There was no JSON column, so I added one with a migration script.
- Deleting a company that still had jobs would cause a database error. I had it block the delete and show a clear message instead.

## How I checked the AI's work

- I ran the tests: all 74 passed.
- I opened the app and tried adding, editing and deleting records myself.

## What I learned

AI saves a lot of time, but it can make mistakes that look correct. I still have to test and review everything it writes.
