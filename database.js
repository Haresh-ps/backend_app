const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, 'doctor_app.db');

const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('Error opening database ' + dbPath + ': ' + err.message);
    } else {
        console.log('Connected to the SQLite database.');

        // Enable foreign keys
        db.run("PRAGMA foreign_keys = ON");

        // Users Table (Simple usage, no hashing for demo if not needed, but good practice)
        db.run(`CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            password TEXT
        )`);

        // Profiles Table
        db.run(`CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            clinic_name TEXT,
            specialization TEXT,
            phone_number TEXT,
            full_name TEXT,
            address TEXT,
            experience_years TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )`);

        // Assessments Table
        db.run(`CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            embryo_count INTEGER,
            embryo_day TEXT,
            culture_duration TEXT,
            questions_data TEXT, -- JSON string for Q1-Q6 answers
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )`);

        // Media Table (Images/Videos)
        db.run(`CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER,
            file_path TEXT,
            file_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(assessment_id) REFERENCES assessments(id)
        )`);

        // Analysis Results Table
        db.run(`CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id INTEGER,
            confidence_score REAL,
            viability_prediction TEXT,
            ai_feedback TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(assessment_id) REFERENCES assessments(id)
        )`);
    }
});

module.exports = db;
