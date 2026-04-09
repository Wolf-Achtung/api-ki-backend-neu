-- Chat Sessions: Konversationeller KI-Fragebogen (PoC Block 1)
-- Neue Tabelle, keine bestehenden Tabellen geaendert.

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Zuordnung
    report_type VARCHAR(20) NOT NULL DEFAULT 'r1',
    lang VARCHAR(5) DEFAULT 'de',
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    briefing_id INTEGER REFERENCES briefings(id) ON DELETE SET NULL,

    -- Consent
    consent_report BOOLEAN DEFAULT FALSE,
    consent_at TIMESTAMPTZ,

    -- State
    collected_fields JSONB DEFAULT '{}'::jsonb,
    field_meta JSONB DEFAULT '{}'::jsonb,
    current_section INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Konversation
    messages JSONB DEFAULT '[]'::jsonb,
    turn_count INTEGER DEFAULT 0,
    conversation_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_activity ON chat_sessions(last_activity_at);
