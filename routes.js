const express = require('express');
const multer = require('multer');
const path = require('path');
const db = require('./database');
const router = express.Router();

// --- Middleware for file uploads ---
// Configure storage
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, 'uploads/')
    },
    filename: function (req, file, cb) {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9)
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname))
    }
});
const upload = multer({ storage: storage });

// --- Helper: Get default user for simple auth ---
// In a real app, you'd extract user from JWT. Here we'll use a default user or create one.
const getUserId = (req) => {
    return 1; // Mock user ID 1
};

// --- AUTH ENDPOINTS ---

router.post('/auth/login/', (req, res) => {
    const { username, password } = req.body;
    // Simple mock login
    console.log(`Login attempt: ${username}`);
    // Check if user exists, if not create for demo? Or just return success.
    // Let's just return a mock token.
    res.json({
        access: "mock_access_token_" + Date.now(),
        refresh: "mock_refresh_token_" + Date.now()
    });
});

router.post('/auth/signup/', (req, res) => {
    const { username, email, password } = req.body;
    console.log(`Signup attempt: ${username}, ${email}`);

    db.run(`INSERT INTO users (username, email, password) VALUES (?, ?, ?)`,
        [username, email, password],
        function (err) {
            if (err) {
                // If user exists, just success for now to avoid blocking
                console.log("User might already exist or error: " + err.message);
                res.status(200).send();
                return;
            }
            res.status(201).send();
        });
});

// --- PROFILE ENDPOINTS ---

const handleProfileUpdate = (req, res) => {
    const userId = getUserId(req);
    const { clinic_name, specialization, phone_number, full_name, address, experience_years } = req.body;

    // Check if profile exists
    db.get(`SELECT id FROM profiles WHERE user_id = ?`, [userId], (err, row) => {
        if (err) { return res.status(500).json({ error: err.message }); }

        if (row) {
            // Update
            db.run(`UPDATE profiles SET clinic_name=?, specialization=?, phone_number=?, full_name=?, address=?, experience_years=? WHERE user_id=?`,
                [clinic_name, specialization, phone_number, full_name, address, experience_years, userId],
                (err) => {
                    if (err) return res.status(500).json({ error: err.message });
                    res.json({ clinic_name, specialization, full_name });
                });
        } else {
            // Insert
            db.run(`INSERT INTO profiles (user_id, clinic_name, specialization, phone_number, full_name, address, experience_years) VALUES (?, ?, ?, ?, ?, ?, ?)`,
                [userId, clinic_name, specialization, phone_number, full_name, address, experience_years],
                (err) => {
                    if (err) return res.status(500).json({ error: err.message });
                    res.json({ clinic_name, specialization, full_name });
                });
        }
    });
};

router.post('/auth/profile/', handleProfileUpdate);
router.put('/auth/profile/', handleProfileUpdate);

router.get('/auth/profile/', (req, res) => {
    const userId = getUserId(req);
    db.get(`SELECT * FROM profiles WHERE user_id = ?`, [userId], (err, row) => {
        if (err) return res.status(500).json({ error: err.message });
        if (row) {
            res.json(row);
        } else {
            res.status(404).json({ error: "Profile not found" });
        }
    });
});

// --- ASSESSMENT ENDPOINTS ---

router.post('/auth/assessments/', (req, res) => {
    const userId = getUserId(req);
    const { embryo_count, embryo_day, culture_duration, questions_data } = req.body;

    // questions_data comes as a Map from Android (JSON object)
    const questionsJson = JSON.stringify(questions_data);

    db.run(`INSERT INTO assessments (user_id, embryo_count, embryo_day, culture_duration, questions_data) VALUES (?, ?, ?, ?, ?)`,
        [userId, embryo_count, embryo_day, culture_duration, questionsJson],
        function (err) {
            if (err) return res.status(500).json({ error: err.message });
            console.log(`Created assessment with ID: ${this.lastID}`);
            res.status(201).json({
                id: this.lastID,
                created_at: new Date().toISOString()
            });
        }
    );
});

router.post('/auth/assessments/:id/analyze/', (req, res) => {
    const assessmentId = req.params.id;
    console.log(`Analyzing assessment ${assessmentId}...`);

    // Mock Analysis
    const result = {
        confidence_score: 95.5,
        viability_prediction: "High Viability",
        ai_feedback: "The embryo shows strong development markers consistent with a 5-day Blastocyst. Inner cell mass and trophectoderm grades appear promising."
    };

    db.run(`INSERT INTO analysis_results (assessment_id, confidence_score, viability_prediction, ai_feedback) VALUES (?, ?, ?, ?)`,
        [assessmentId, result.confidence_score, result.viability_prediction, result.ai_feedback],
        function (err) {
            if (err) return res.status(500).json({ error: err.message });
            res.json(result);
        }
    );
});

// --- MEDIA UPLOAD ---

router.post('/auth/upload/', upload.single('file'), (req, res) => {
    // Android sends 'assessment_id' as a part
    let assessmentId = req.body.assessment_id;
    // If it comes as a string with quotes (sometimes happens with Retrofit standard converters depending on setup), clean it.
    if (assessmentId && typeof assessmentId === 'string') {
        assessmentId = assessmentId.replace(/"/g, '');
    }

    if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
    }

    const filePath = req.file.path.replace(/\\\\/g, '/'); // Fix windows paths
    const fileType = req.file.mimetype;

    console.log(`File uploaded: ${filePath} for Assessment ${assessmentId}`);

    db.run(`INSERT INTO media (assessment_id, file_path, file_type) VALUES (?, ?, ?)`,
        [assessmentId, filePath, fileType],
        function (err) {
            if (err) return res.status(500).json({ error: err.message });

            // Construct a URL to return (simplified)
            // Assuming server runs on localhost:8000
            const fileUrl = `http://10.0.2.2:8000/${filePath}`;
            res.status(201).json({
                id: this.lastID,
                file_url: fileUrl
            });
        }
    );
});

module.exports = router;
