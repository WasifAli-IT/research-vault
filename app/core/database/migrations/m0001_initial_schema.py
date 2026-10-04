"""
Migration 0001: initial schema.

Creates all core tables (categories, research_projects, sections,
notes, sources) plus the FTS5 full-text search index and the
triggers that keep it synchronized.
"""

from __future__ import annotations

import sqlite3

VERSION = 1


def upgrade(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE categories (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            color         TEXT,
            position      INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        );

        CREATE TABLE research_projects (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            title         TEXT NOT NULL,
            description   TEXT NOT NULL DEFAULT '',
            category_id   INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            is_favorite   INTEGER NOT NULL DEFAULT 0,
            position      INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        );

        CREATE TABLE sections (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            research_id   INTEGER NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
            title         TEXT NOT NULL,
            content       TEXT NOT NULL DEFAULT '',
            position      INTEGER NOT NULL DEFAULT 0,
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        );

        CREATE TABLE notes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            research_id   INTEGER NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
            section_id    INTEGER REFERENCES sections(id) ON DELETE SET NULL,
            content       TEXT NOT NULL,
            created_at    TEXT NOT NULL,
            updated_at    TEXT NOT NULL
        );

        CREATE TABLE sources (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            research_id       INTEGER NOT NULL REFERENCES research_projects(id) ON DELETE CASCADE,
            title             TEXT NOT NULL,
            url               TEXT,
            author            TEXT,
            publication_date  TEXT,
            notes             TEXT NOT NULL DEFAULT '',
            created_at        TEXT NOT NULL,
            updated_at        TEXT NOT NULL
        );

        CREATE INDEX idx_research_category ON research_projects(category_id);
        CREATE INDEX idx_sections_research ON sections(research_id, position);
        CREATE INDEX idx_notes_research    ON notes(research_id);
        CREATE INDEX idx_notes_section     ON notes(section_id);
        CREATE INDEX idx_sources_research  ON sources(research_id);

        CREATE VIRTUAL TABLE search_index USING fts5(
            entity_type UNINDEXED,
            entity_id UNINDEXED,
            research_id UNINDEXED,
            title,
            body,
            tokenize = 'porter unicode61'
        );

        -- Keep search_index in sync with research_projects
        CREATE TRIGGER trg_research_ai AFTER INSERT ON research_projects BEGIN
            INSERT INTO search_index (entity_type, entity_id, research_id, title, body)
            VALUES ('research', new.id, new.id, new.title, new.description);
        END;

        CREATE TRIGGER trg_research_au AFTER UPDATE ON research_projects BEGIN
            DELETE FROM search_index WHERE entity_type = 'research' AND entity_id = old.id;
            INSERT INTO search_index (entity_type, entity_id, research_id, title, body)
            VALUES ('research', new.id, new.id, new.title, new.description);
        END;

        CREATE TRIGGER trg_research_ad AFTER DELETE ON research_projects BEGIN
            DELETE FROM search_index WHERE entity_type = 'research' AND entity_id = old.id;
        END;

        -- Keep search_index in sync with sections
        CREATE TRIGGER trg_section_ai AFTER INSERT ON sections BEGIN
            INSERT INTO search_index (entity_type, entity_id, research_id, title, body)
            VALUES ('section', new.id, new.research_id, new.title, new.content);
        END;

        CREATE TRIGGER trg_section_au AFTER UPDATE ON sections BEGIN
            DELETE FROM search_index WHERE entity_type = 'section' AND entity_id = old.id;
            INSERT INTO search_index (entity_type, entity_id, research_id, title, body)
            VALUES ('section', new.id, new.research_id, new.title, new.content);
        END;

        CREATE TRIGGER trg_section_ad AFTER DELETE ON sections BEGIN
            DELETE FROM search_index WHERE entity_type = 'section' AND entity_id = old.id;
        END;

        -- Keep search_index in sync with notes
        CREATE TRIGGER trg_note_ai AFTER INSERT ON notes BEGIN
            INSERT INTO search_index (entity_type, entity_id, research_id, title, body)
            VALUES ('note', new.id, new.research_id, '', new.content);
        END;

        CREATE TRIGGER trg_note_au AFTER UPDATE ON notes BEGIN
            DELETE FROM search_index WHERE entity_type = 'note' AND entity_id = old.id;
            INSERT INTO search_index (entity_type, entity_id, research_id, title, body)
            VALUES ('note', new.id, new.research_id, '', new.content);
        END;

        CREATE TRIGGER trg_note_ad AFTER DELETE ON notes BEGIN
            DELETE FROM search_index WHERE entity_type = 'note' AND entity_id = old.id;
        END;

        -- Keep search_index in sync with sources
        CREATE TRIGGER trg_source_ai AFTER INSERT ON sources BEGIN
            INSERT INTO search_index (entity_type, entity_id, research_id, title, body)
            VALUES ('source', new.id, new.research_id, new.title, new.notes);
        END;

        CREATE TRIGGER trg_source_au AFTER UPDATE ON sources BEGIN
            DELETE FROM search_index WHERE entity_type = 'source' AND entity_id = old.id;
            INSERT INTO search_index (entity_type, entity_id, research_id, title, body)
            VALUES ('source', new.id, new.research_id, new.title, new.notes);
        END;

        CREATE TRIGGER trg_source_ad AFTER DELETE ON sources BEGIN
            DELETE FROM search_index WHERE entity_type = 'source' AND entity_id = old.id;
        END;
        """
    )
    