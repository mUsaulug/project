-- Migration: Drop originalText column for KVKK compliance
-- Run this on existing databases before deploying new version

-- Step 1: Backup existing data (optional, for audit)
-- CREATE TABLE complaints_backup AS SELECT * FROM complaints;

-- Step 2: Drop the column
ALTER TABLE complaints DROP COLUMN IF EXISTS original_text;

-- Note: JPA with ddl-auto=update will handle schema for new deployments
-- This script is for migrating existing databases
